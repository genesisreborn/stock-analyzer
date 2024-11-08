from flask import Blueprint, render_template, jsonify, request, send_file, current_app
from app.services.stock_service import StockService
from app.services.technical_analysis import TechnicalAnalysis
from app.models.stock import Stock, CrossoverEvent
import yfinance as yf
import csv
from io import BytesIO
from flask_login import login_required
from app import db, socketio
import threading

main = Blueprint('main', __name__)

# Global variable to track update status
update_status = {
    'is_updating': False,
    'progress': 0,
    'total': 0
}

def update_stocks_background(symbols, app):
    """Background task to update stocks"""
    global update_status
    update_status['total'] = len(symbols)
    update_status['progress'] = 0
    
    # Create a new application context for this thread
    with app.app_context():
        for i, symbol in enumerate(symbols):
            try:
                # Set last_updated to None to force update
                stock = Stock.query.filter_by(symbol=symbol).first()
                if stock:
                    stock.last_updated = None
                    db.session.commit()
                
                StockService.update_stock_data(symbol, period='max', ema_period=14, sma_period=50)
                
                # Update progress
                update_status['progress'] = i + 1
                socketio.emit('update_progress', {
                    'progress': update_status['progress'],
                    'total': update_status['total']
                })
                
            except Exception as e:
                print(f"Error updating {symbol}: {str(e)}")
        
        update_status['is_updating'] = False
        socketio.emit('update_complete')

@main.route('/')
def dashboard():
    # Get all stocks with signals (either bullish or bearish)
    stocks_with_signals = (
        Stock.query
        .filter(Stock.crossover_type.in_(['bullish', 'bearish']))
        .order_by(Stock.last_crossover.desc())
        .all()
    )

    # Get recent crossovers with stock information
    recent_crossovers = (
        CrossoverEvent.query
        .join(Stock)
        .order_by(CrossoverEvent.timestamp.desc())
        .limit(10)
        .all()
    )

    # Get summary statistics
    total_stocks = Stock.query.count()
    bullish_count = Stock.query.filter_by(crossover_type='bullish').count()
    bearish_count = Stock.query.filter_by(crossover_type='bearish').count()

    # Crossover criteria information
    crossover_info = {
        'ema_period': 14,
        'sma_period': 50,
        'bullish_condition': 'EMA crosses above SMA',
        'bearish_condition': 'EMA crosses below SMA'
    }

    return render_template('dashboard.html',
                         stocks_with_signals=stocks_with_signals,
                         recent_crossovers=recent_crossovers,
                         total_stocks=total_stocks,
                         bullish_count=bullish_count,
                         bearish_count=bearish_count,
                         crossover_info=crossover_info)

@main.route('/stocks')
def stock_list():
    stocks = Stock.query.all()
    print(f"Fetched {len(stocks)} stocks from the database.")  # Debug statement
    return render_template('stock_list.html', stocks=stocks)

@main.route('/stock/<symbol>')
def stock_detail(symbol):
    # Get interval from query parameters, default to '1d'
    selected_interval = request.args.get('interval', '1d')
    stock = Stock.query.filter_by(symbol=symbol).first_or_404()
    
    # Get historical data with selected interval
    ticker = yf.Ticker(symbol)
    
    # Always fetch YTD data with the selected interval
    df = ticker.history(period='ytd', interval=selected_interval)
    
    # Calculate indicators with EMA 14 and SMA 50
    df = TechnicalAnalysis.calculate_indicators(df, ema_period=14, sma_period=50)
    
    # Create chart
    chart_json = TechnicalAnalysis.create_chart(df, symbol, ema_period=14, sma_period=50)
    
    # Define available intervals for dropdown
    intervals = [
        {'value': '1m', 'label': '1 Minute'},
        {'value': '5m', 'label': '5 Minutes'},
        {'value': '15m', 'label': '15 Minutes'},
        {'value': '30m', 'label': '30 Minutes'},
        {'value': '1h', 'label': '1 Hour'},
        {'value': '4h', 'label': '4 Hours'},
        {'value': '1d', 'label': '1 Day'}
    ]
    
    return render_template('stock_detail.html',
                         stock=stock,
                         chart_json=chart_json,
                         ema_period=14,
                         sma_period=50,
                         intervals=intervals,
                         selected_interval=selected_interval)

@main.route('/api/update_stocks')
def update_stocks():
    """Start the update process in a background thread"""
    global update_status
    
    if update_status['is_updating']:
        return jsonify({
            'status': 'in_progress',
            'message': 'Update already in progress',
            'progress': update_status['progress'],
            'total': update_status['total']
        })
    
    update_status['is_updating'] = True
    symbols = StockService.get_sp500_symbols()
    
    # Get current app instance and pass it to the background thread
    app = current_app._get_current_object()
    
    # Start background thread
    thread = threading.Thread(target=update_stocks_background, args=(symbols, app))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'status': 'started',
        'message': 'Update process started'
    })

@main.route('/api/update_status')
def get_update_status():
    """Get the current status of the update process"""
    return jsonify({
        'is_updating': update_status['is_updating'],
        'progress': update_status['progress'],
        'total': update_status['total']
    })

@main.route('/export/<symbol>')
@login_required
def export_stock_data(symbol):
    stock = Stock.query.filter_by(symbol=symbol).first_or_404()
    
    # Get historical data
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="1y")
    
    # Calculate indicators
    df = TechnicalAnalysis.calculate_indicators(df, ema_period=14, sma_period=50)
    
    # Create CSV in binary mode
    output = BytesIO()
    df.to_csv(output, index=True, encoding='utf-8')
    output.seek(0)
    
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{symbol}_data.csv'
    )

@main.route('/api/refresh/<symbol>')
def refresh_stock(symbol):
    """Endpoint to manually refresh stock data"""
    try:
        StockService.update_stock_data(symbol, period='max', ema_period=14, sma_period=50)
        return jsonify({'status': 'success', 'message': f'Successfully refreshed data for {symbol}'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500