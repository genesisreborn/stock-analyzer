import yfinance as yf
import pandas as pd
from app.models.stock import Stock, CrossoverEvent
from app import db
from datetime import datetime

class StockService:
    @staticmethod
    def get_sp500_symbols():
        # You might want to use a proper S&P 500 API here
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        df = tables[0]
        
        # Clean up symbols - replace dots with hyphens for special cases
        symbols = []
        for symbol in df['Symbol'].tolist():
            # Handle special cases
            if symbol in ['BRK.B', 'BF.B']:
                symbol = symbol.replace('.', '-')  # Convert to BRK-B and BF-B
            symbols.append(symbol)
        
        return symbols

    @staticmethod
    def update_stock_data(symbol, period='max', ema_period=14, sma_period=50):
        stock_data = Stock.query.filter_by(symbol=symbol).first()
        
        # Check if stock data already exists and was updated recently
        REFRESH_HOURS = 4  # Refresh every 4 hours
        
        if stock_data and stock_data.last_updated:
            time_since_update = (datetime.now() - stock_data.last_updated).total_seconds()
            if time_since_update < REFRESH_HOURS * 3600:
                print(f"Data for {symbol} is already up to date.")
                return stock_data

        stock = yf.Ticker(symbol)
        
        # Get company info
        try:
            info = stock.info
            company_name = info.get('longName', 'N/A')
        except Exception as e:
            print(f"Error fetching company info for {symbol}: {str(e)}")
            company_name = 'N/A'
        
        hist = stock.history(period=period)  # Fetch data for the maximum available period
        
        if hist.empty:
            print(f"No data for {symbol}")  # Debug statement
            return None

        current_price = hist['Close'].iloc[-1]
        
        # Calculate EMA 14 and SMA 50
        ema = hist['Close'].ewm(span=ema_period).mean()
        sma = hist['Close'].rolling(window=sma_period).mean()

        # Check for crossover
        if len(ema) >= 2 and len(sma) >= 2:
            # Check last two points for crossover
            if (ema.iloc[-2] <= sma.iloc[-2] and ema.iloc[-1] > sma.iloc[-1]):
                crossover_type = 'bullish'
                has_crossover = True
            elif (ema.iloc[-2] >= sma.iloc[-2] and ema.iloc[-1] < sma.iloc[-1]):
                crossover_type = 'bearish'
                has_crossover = True
            else:
                has_crossover = False
        else:
            has_crossover = False

        # Update database
        if not stock_data:
            stock_data = Stock(symbol=symbol)
            db.session.add(stock_data)
        
        stock_data.company_name = company_name  # Update company name
        stock_data.last_price = current_price
        stock_data.last_updated = datetime.now()
        stock_data.ema = ema.iloc[-1]  # Store latest EMA value
        stock_data.sma = sma.iloc[-1]  # Store latest SMA value
        
        # Commit the stock data first to get the ID
        db.session.commit()
        
        if has_crossover:
            current_time = datetime.now()
            stock_data.last_crossover = current_time
            stock_data.crossover_price = current_price
            stock_data.crossover_type = crossover_type

            # Create crossover event with the same timestamp
            event = CrossoverEvent(
                stock_id=stock_data.id,
                price=current_price,
                crossover_type=crossover_type,
                timestamp=current_time  # Explicitly set the timestamp
            )
            db.session.add(event)
            db.session.commit()

        return stock_data