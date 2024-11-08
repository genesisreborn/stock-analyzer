from app import socketio
from flask_socketio import emit
from app.services.stock_service import StockService
import threading
import time

def background_update():
    while True:
        symbols = StockService.get_sp500_symbols()
        for symbol in symbols:
            stock_data = StockService.update_stock_data(symbol)
            if stock_data and stock_data.last_crossover:
                socketio.emit('crossover_alert', {
                    'symbol': stock_data.symbol,
                    'type': stock_data.crossover_type,
                    'price': stock_data.crossover_price,
                    'time': stock_data.last_crossover.strftime('%Y-%m-%d %H:%M:%S')
                })
        time.sleep(60)  # Update every minute

@socketio.on('connect')
def handle_connect():
    if not hasattr(socketio, 'background_task'):
        socketio.background_task = threading.Thread(target=background_update)
        socketio.background_task.daemon = True
        socketio.background_task.start() 