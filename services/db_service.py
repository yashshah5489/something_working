import logging
from datetime import datetime, timedelta
from app import db
from models import User, StockData, NewsItem, BookInsight, UserQuery
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class PostgreSQLService:
    """
    Service for interacting with PostgreSQL
    """
    def __init__(self):
        self.db = db
        
    # User related methods
    def create_user(self, username, email, password_hash):
        """Create a new user in the database"""
        try:
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                created_at=datetime.utcnow(),
                preferences={
                    "stock_watchlist": [],
                    "favorite_sectors": [],
                    "risk_profile": "Moderate",
                    "investment_horizon": "Medium Term",
                    "dark_mode": True
                }
            )
            db.session.add(user)
            db.session.commit()
            return user.id
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error creating user: {e}")
            return None

    def get_user_by_email(self, email):
        """Retrieve a user by email"""
        try:
            return User.query.filter_by(email=email).first()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving user by email: {e}")
            return None
            
    def get_user_by_id(self, user_id):
        """Retrieve a user by ID"""
        try:
            return User.query.get(user_id)
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving user by ID: {e}")
            return None

    def update_user_preferences(self, user_id, preferences):
        """Update user preferences"""
        try:
            user = User.query.get(user_id)
            if user:
                user.preferences = preferences
                db.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error updating user preferences: {e}")
            return False

    # Stock data methods
    def save_stock_data(self, stock_data_dict):
        """Save or update stock data"""
        try:
            # Check if stock exists
            stock = StockData.query.filter_by(
                symbol=stock_data_dict.get("symbol"),
                exchange=stock_data_dict.get("exchange")
            ).first()
            
            if stock:
                # Update existing stock
                for key, value in stock_data_dict.items():
                    if hasattr(stock, key):
                        setattr(stock, key, value)
                stock.last_updated = datetime.utcnow()
            else:
                # Create new stock
                stock = StockData(
                    symbol=stock_data_dict.get("symbol"),
                    exchange=stock_data_dict.get("exchange"),
                    name=stock_data_dict.get("name"),
                    sector=stock_data_dict.get("sector"),
                    current_price=stock_data_dict.get("current_price"),
                    day_change=stock_data_dict.get("day_change"),
                    volume=stock_data_dict.get("volume"),
                    high_52week=stock_data_dict.get("high_52week"),
                    low_52week=stock_data_dict.get("low_52week"),
                    historical_data=stock_data_dict.get("historical_data", []),
                    last_updated=datetime.utcnow()
                )
                db.session.add(stock)
            
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error saving stock data: {e}")
            return False

    def get_stock_data(self, symbol, exchange):
        """Retrieve stock data for a specific symbol and exchange"""
        try:
            return StockData.query.filter_by(symbol=symbol, exchange=exchange).first()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving stock data: {e}")
            return None

    def get_stocks_by_sector(self, sector):
        """Retrieve all stocks in a given sector"""
        try:
            return StockData.query.filter_by(sector=sector).all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving stocks by sector: {e}")
            return []

    def get_trending_stocks(self, limit=10):
        """Get trending stocks based on recent performance"""
        try:
            # Get top gainers and losers
            gainers_limit = limit // 2
            losers_limit = limit - gainers_limit
            
            gainers = StockData.query.order_by(StockData.day_change.desc()).limit(gainers_limit).all()
            losers = StockData.query.order_by(StockData.day_change.asc()).limit(losers_limit).all()
            
            return {"gainers": gainers, "losers": losers}
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving trending stocks: {e}")
            return {"gainers": [], "losers": []}

    # News methods
    def save_news_item(self, news_item_dict):
        """Save a news item to the database"""
        try:
            # Check if news with same title and source already exists
            existing = NewsItem.query.filter_by(
                title=news_item_dict.get("title"),
                source=news_item_dict.get("source")
            ).first()
            
            if not existing:
                # Create new news item
                news_item = NewsItem(
                    title=news_item_dict.get("title"),
                    source=news_item_dict.get("source"),
                    url=news_item_dict.get("url"),
                    published_date=news_item_dict.get("published_date"),
                    content=news_item_dict.get("content"),
                    summary=news_item_dict.get("summary"),
                    sentiment=news_item_dict.get("sentiment"),
                    relevance_score=news_item_dict.get("relevance_score"),
                    related_stocks=news_item_dict.get("related_stocks", []),
                    created_at=datetime.utcnow()
                )
                db.session.add(news_item)
                db.session.commit()
                return news_item.id
            return existing.id
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error saving news item: {e}")
            return None

    def get_recent_news(self, limit=20):
        """Retrieve recent news"""
        try:
            return NewsItem.query.order_by(NewsItem.published_date.desc()).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving recent news: {e}")
            return []

    def get_news_by_stock(self, stock_symbol, limit=10):
        """Retrieve news related to a specific stock"""
        try:
            # This is a simplification - in a real implementation, you would need 
            # a more sophisticated query to search within the related_stocks JSON array
            all_news = NewsItem.query.order_by(NewsItem.published_date.desc()).all()
            relevant_news = []
            
            for news in all_news:
                if stock_symbol in news.related_stocks:
                    relevant_news.append(news)
                    if len(relevant_news) >= limit:
                        break
            
            return relevant_news
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving news by stock: {e}")
            return []

    # Book insights methods
    def save_book_insight(self, book_insight_dict):
        """Save book insight data"""
        try:
            # Check if book exists
            book = BookInsight.query.filter_by(book_title=book_insight_dict.get("book_title")).first()
            
            if book:
                # Update existing book
                for key, value in book_insight_dict.items():
                    if hasattr(book, key):
                        setattr(book, key, value)
            else:
                # Create new book insight
                book = BookInsight(
                    book_title=book_insight_dict.get("book_title"),
                    author=book_insight_dict.get("author"),
                    topics=book_insight_dict.get("topics", []),
                    insights=book_insight_dict.get("insights", []),
                    relevance_categories=book_insight_dict.get("relevance_categories", []),
                    summary=book_insight_dict.get("summary"),
                    created_at=datetime.utcnow()
                )
                db.session.add(book)
            
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error saving book insight: {e}")
            return False

    def get_book_insights(self, topic=None):
        """Get book insights, optionally filtered by topic"""
        try:
            if topic:
                # This is a simplification - in a real implementation, you would need 
                # a more sophisticated query to search within the topics JSON array
                all_books = BookInsight.query.all()
                return [book for book in all_books if topic in book.topics]
            else:
                return BookInsight.query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving book insights: {e}")
            return []

    # User queries and responses
    def save_user_query(self, user_query_dict):
        """Save a user query and its response"""
        try:
            # Create new query
            user_query = UserQuery(
                user_id=user_query_dict.get("user_id"),
                query_text=user_query_dict.get("query_text"),
                query_type=user_query_dict.get("query_type"),
                response=user_query_dict.get("response"),
                sources=user_query_dict.get("sources", []),
                confidence_score=user_query_dict.get("confidence_score"),
                created_at=datetime.utcnow()
            )
            db.session.add(user_query)
            db.session.commit()
            return user_query.id
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error saving user query: {e}")
            return None

    def get_user_query_history(self, user_id, limit=20):
        """Get query history for a user"""
        try:
            return UserQuery.query.filter_by(user_id=user_id).order_by(UserQuery.created_at.desc()).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving user query history: {e}")
            return []

    def update_query_feedback(self, query_id, feedback):
        """Update feedback for a query"""
        try:
            query = UserQuery.query.get(query_id)
            if query:
                query.feedback = feedback
                db.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error updating query feedback: {e}")
            return False

# Create instance of the service
db_service = PostgreSQLService()
