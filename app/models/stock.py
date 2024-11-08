from datetime import datetime
from app import db

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), unique=True, nullable=False)
    company_name = db.Column(db.String(200))
    last_price = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    ema = db.Column(db.Float)
    sma = db.Column(db.Float)
    last_crossover = db.Column(db.DateTime)
    crossover_price = db.Column(db.Float)
    crossover_type = db.Column(db.String(10))
    
    crossover_events = db.relationship('CrossoverEvent', backref='stock', lazy=True)

    __table_args__ = (
        db.Index('idx_symbol', 'symbol'),
        db.Index('idx_crossover_type', 'crossover_type'),
        db.Index('idx_last_crossover', 'last_crossover'),
    )

class CrossoverEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    price = db.Column(db.Float)
    crossover_type = db.Column(db.String(10))