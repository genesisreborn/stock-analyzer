import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    # Main database for stocks
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///stocks.db')
    # User database for authentication
    SQLALCHEMY_BINDS = {
        'users': 'sqlite:///users.db'
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False