from app import create_app, socketio
from app.routes.main import update_stocks
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from app.models.stock import Stock
import threading

app = create_app()
scheduler = BackgroundScheduler()

def update_stocks_async():
    """Run update_stocks in a separate thread with app context"""
    with app.app_context():
        try:
            update_stocks()
        except Exception as e:
            print(f"Error in update_stocks_async: {str(e)}")

def scheduled_update():
    with app.app_context():
        print(f"Checking for updates at {datetime.now()}")
        
        # Check if we have any stocks in the database
        stocks = Stock.query.all()
        if not stocks:
            print("No stocks found in database. Performing initial update...")
            thread = threading.Thread(target=update_stocks_async)
            thread.daemon = True
            thread.start()
            return

        # Check if any stock needs updating (older than 4 hours)
        current_time = datetime.now()
        update_threshold = current_time - timedelta(hours=4)
        
        needs_update = False
        for stock in stocks:
            if not stock.last_updated or stock.last_updated < update_threshold:
                needs_update = True
                break

        if needs_update:
            print("Some stocks need updating. Performing update...")
            thread = threading.Thread(target=update_stocks_async)
            thread.daemon = True
            thread.start()
        else:
            print("All stocks are up to date. Skipping update.")

# Schedule the update to run every 4 hours
scheduler.add_job(func=scheduled_update, trigger="interval", hours=4)
scheduler.start()

# Initial check on startup
with app.app_context():
    scheduled_update()

if __name__ == '__main__':
    socketio.run(app, debug=True) 