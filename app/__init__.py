from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_migrate import Migrate
from app.config import Config

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()
migrate = Migrate()

@login_manager.user_loader
def load_user(id):
    from app.models.user import User
    return User.query.get(int(id))

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'

    from app.routes.main import main
    from app.routes.auth import auth
    app.register_blueprint(main)
    app.register_blueprint(auth)

    with app.app_context():
        # Only create tables if they don't exist
        db.create_all()

    return app 