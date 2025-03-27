from datetime import datetime
from app import db
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Boolean

class User(UserMixin, db.Model):
    """
    User model for PostgreSQL
    """
    __tablename__ = 'users'
    
    id = db.Column(Integer, primary_key=True)
    username = db.Column(String(64), unique=True, nullable=False)
    email = db.Column(String(120), unique=True, nullable=False)
    password_hash = db.Column(String(256), nullable=False)
    preferences = db.Column(db.JSON, default={
        "stock_watchlist": [],
        "favorite_sectors": [],
        "risk_profile": "Moderate",
        "investment_horizon": "Medium Term",
        "dark_mode": True
    })
    created_at = db.Column(DateTime, default=datetime.utcnow)
    last_login = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'

class StockData(db.Model):
    """
    Stock data model for PostgreSQL
    """
    __tablename__ = 'stock_data'
    
    id = db.Column(Integer, primary_key=True)
    symbol = db.Column(String(20), nullable=False, index=True)
    exchange = db.Column(String(10), nullable=False)  # NSE or BSE
    name = db.Column(String(100), nullable=False)
    sector = db.Column(String(50))
    current_price = db.Column(Float)
    day_change = db.Column(Float)
    volume = db.Column(Float)
    high_52week = db.Column(Float)
    low_52week = db.Column(Float)
    historical_data = db.Column(db.JSON, default=[])  # List of daily price points
    last_updated = db.Column(DateTime, default=datetime.utcnow)
    
    # Unique constraint on symbol and exchange
    __table_args__ = (db.UniqueConstraint('symbol', 'exchange', name='uix_stock_symbol_exchange'),)
    
    def __repr__(self):
        return f'<Stock {self.symbol}:{self.exchange}>'

class NewsItem(db.Model):
    """
    News item model for PostgreSQL
    """
    __tablename__ = 'news_items'
    
    id = db.Column(Integer, primary_key=True)
    title = db.Column(String(200), nullable=False)
    source = db.Column(String(100), nullable=False)
    url = db.Column(String(500), nullable=False, unique=True)
    published_date = db.Column(DateTime, nullable=False)
    content = db.Column(Text)
    summary = db.Column(Text)
    sentiment = db.Column(String(20))  # positive, negative, neutral
    relevance_score = db.Column(Float)  # 0-1 score of relevance to finance
    related_stocks = db.Column(db.JSON, default=[])  # List of stock symbols mentioned
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<News {self.title[:30]}...>'

class BookInsight(db.Model):
    """
    Book insight model for PostgreSQL
    """
    __tablename__ = 'book_insights'
    
    id = db.Column(Integer, primary_key=True)
    book_title = db.Column(String(200), nullable=False, unique=True)
    author = db.Column(String(100), nullable=False)
    topics = db.Column(db.JSON, default=[])  # List of finance topics covered
    insights = db.Column(db.JSON, default=[])  # Key insights from the book
    relevance_categories = db.Column(db.JSON, default=[])  # e.g., "Investing", "Tax Planning"
    summary = db.Column(Text)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Book {self.book_title}>'

class UserQuery(db.Model):
    """
    User query model for PostgreSQL
    """
    __tablename__ = 'user_queries'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=True)
    query_text = db.Column(Text, nullable=False)
    query_type = db.Column(String(50), nullable=False)  # stock_analysis, general_finance, book_recommendation
    response = db.Column(Text, nullable=False)
    sources = db.Column(db.JSON, default=[])  # List of sources used for response
    confidence_score = db.Column(Float)  # 0-1 score of LLM confidence
    feedback = db.Column(Boolean, nullable=True)  # User feedback on response quality
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Query {self.query_text[:30]}...>'
