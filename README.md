# Stock Analyzer V1

## Features
- Real-time stock data fetching and analysis
- EMA (14) and SMA (50) crossover detection
- User authentication system
- Dashboard with signals and statistics
- Multiple timeframe analysis
- Export functionality
- Progress tracking for updates
- Separate databases for stocks and users

## Database Structure
### stocks.db
- Stock table: Basic stock information and latest data
- CrossoverEvent table: Historical crossover events

### users.db
- User table: Authentication and user management

## Key Components
- Flask web framework
- SQLAlchemy for database management
- yfinance for stock data
- Plotly for charts
- Socket.IO for real-time updates
- Flask-Login for authentication

## Installation
1. Create virtual environment: 
