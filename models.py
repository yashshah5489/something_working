from datetime import datetime
from app import db
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Boolean

# Define models in the correct order for SQLAlchemy relationships

class User(UserMixin, db.Model):
    """
    User model for PostgreSQL
    """
    __tablename__ = 'users'
    
    id = db.Column(Integer, primary_key=True)
    username = db.Column(String(64), unique=True, nullable=False)
    email = db.Column(String(120), unique=True, nullable=False)
    password_hash = db.Column(String(256), nullable=False)
    
    # User preferences
    preferences = db.Column(db.JSON, default={
        "stock_watchlist": [],
        "favorite_sectors": [],
        "risk_profile": "Moderate",
        "investment_horizon": "Medium Term",
        "dark_mode": True,
        "daily_tip": True,
        "learning_notifications": True
    })
    
    # Personal profile for personalization (all optional)
    personal_profile = db.Column(db.JSON, default={
        "age_group": None,                 # "18-25", "26-35", "36-45", "46-55", "56+"
        "income_bracket": None,            # "0-5L", "5L-10L", "10L-15L", "15L-25L", "25L+"
        "occupation": None,                # Free text
        "industry": None,                  # Free text
        "location": None,                  # City/State
        "experience_level": "Beginner",    # "Beginner", "Intermediate", "Advanced"
        "financial_goals": [],             # ["Retirement", "House", "Education", "Wealth growth"]
        "existing_investments": [],        # ["Stocks", "MF", "FD", "Real Estate"]
        "monthly_expenses": None,          # Approximate value
        "loan_emi": None,                  # Approximate value
        "risk_tolerance_score": 5,         # 1-10 scale
        "investment_timeline": None,       # Years
        "tax_bracket": None,               # Tax slab
        "preferred_learning_style": "Text" # "Text", "Video", "Interactive"
    })
    
    # Learning progress and bookmarks
    learning_progress = db.Column(db.JSON, default={
        "completed_topics": [],
        "bookmarked_resources": [],
        "quiz_scores": {},
        "current_learning_path": "Basics",
        "difficulty_level": "Beginner"
    })
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    last_login = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_daily_tip = db.Column(DateTime, default=datetime.utcnow)
    
    # Note: Relationships are defined after all models have been declared
    # They will be added at the end of the file

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
        
class DailyTip(db.Model):
    """
    Daily financial tips for users
    """
    __tablename__ = 'daily_tips'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=True)  # If NULL, it's a global tip
    tip_text = db.Column(Text, nullable=False)
    tip_title = db.Column(String(200), nullable=False)
    tip_category = db.Column(String(50), nullable=False)  # investing, saving, tax, etc.
    tip_difficulty = db.Column(String(20), default="Beginner")  # Beginner, Intermediate, Advanced
    is_personalized = db.Column(Boolean, default=False)
    read = db.Column(Boolean, default=False)  # Track if user has read this tip
    saved = db.Column(Boolean, default=False)  # Track if user has saved this tip
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Tip {self.tip_title[:30]}...>'

class LearningResource(db.Model):
    """
    Financial learning resources
    """
    __tablename__ = 'learning_resources'
    
    id = db.Column(Integer, primary_key=True)
    title = db.Column(String(200), nullable=False)
    description = db.Column(Text, nullable=False)
    content = db.Column(Text, nullable=False)  # Could be text content or embedded links
    resource_type = db.Column(String(20), nullable=False)  # article, video, quiz, infographic
    topic = db.Column(String(100), nullable=False, index=True)  # Topic categorization
    subtopic = db.Column(String(100))  # More specific categorization
    difficulty_level = db.Column(String(20), nullable=False, default="Beginner")  # Beginner, Intermediate, Advanced
    duration_minutes = db.Column(Integer, default=5)  # Estimated time to complete
    prerequisites = db.Column(db.JSON, default=[])  # List of prerequisite resource IDs
    thumbnail_url = db.Column(String(500))
    external_url = db.Column(String(500))  # External resource link
    is_premium = db.Column(Boolean, default=False)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Resource {self.title[:30]}...>'

class LearningPath(db.Model):
    """
    Organized learning paths for different financial topics
    """
    __tablename__ = 'learning_paths'
    
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False, unique=True)
    description = db.Column(Text, nullable=False)
    target_audience = db.Column(String(50), nullable=False)  # Beginners, Professionals, etc.
    difficulty_level = db.Column(String(20), nullable=False)
    estimated_days = db.Column(Integer, default=30)
    topics_covered = db.Column(db.JSON, default=[])  # List of topics
    resource_sequence = db.Column(db.JSON, default=[])  # Ordered list of resource IDs
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Path {self.name}>'

class LearningBookmark(db.Model):
    """
    User bookmarks for learning resources
    """
    __tablename__ = 'learning_bookmarks'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=False)
    resource_id = db.Column(Integer, ForeignKey('learning_resources.id'), nullable=False)
    notes = db.Column(Text)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'resource_id', name='uix_user_resource_bookmark'),)
    
    def __repr__(self):
        return f'<Bookmark User:{self.user_id} Resource:{self.resource_id}>'

class LearningProgress(db.Model):
    """
    Tracking user progress through learning resources
    """
    __tablename__ = 'learning_progress'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, ForeignKey('users.id'), nullable=False)
    resource_id = db.Column(Integer, ForeignKey('learning_resources.id'), nullable=False)
    path_id = db.Column(Integer, ForeignKey('learning_paths.id'), nullable=True)
    completion_percentage = db.Column(Float, default=0.0)
    is_completed = db.Column(Boolean, default=False)
    quiz_score = db.Column(Float, nullable=True)  # If resource has an assessment
    time_spent_minutes = db.Column(Integer, default=0)
    last_accessed = db.Column(DateTime, default=datetime.utcnow)
    completed_at = db.Column(DateTime, nullable=True)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'resource_id', name='uix_user_resource_progress'),)
    
    def __repr__(self):
        return f'<Progress User:{self.user_id} Resource:{self.resource_id} {self.completion_percentage}%>'
        
# Add relationships after all models have been defined
User.daily_tips = db.relationship('DailyTip', backref='user', lazy='dynamic')
User.learning_bookmarks = db.relationship('LearningBookmark', backref='user', lazy='dynamic')
User.learning_progress_records = db.relationship('LearningProgress', backref='user', lazy='dynamic')
User.queries = db.relationship('UserQuery', backref='user', lazy='dynamic')
