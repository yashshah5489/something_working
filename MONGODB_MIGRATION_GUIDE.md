# MongoDB Migration Guide

This guide provides instructions for migrating the Smart Financial Analyzer application from PostgreSQL to MongoDB. Follow these steps when you're ready to implement the migration.

## Prerequisites

1. Install MongoDB dependencies:
   ```bash
   pip install pymongo dnspython
   ```

2. Set up MongoDB connection:
   - For local development: Install MongoDB and run it locally
   - For production: Set up a MongoDB Atlas account or other MongoDB hosting

## Step 1: Update Configuration

Create a MongoDB configuration in `config.py`:

```python
# MongoDB Configuration
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "financial_analyzer")
```

## Step 2: Create MongoDB Service

Create a new MongoDB service in `services/mongodb_service.py`:

```python
import os
import logging
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from bson.objectid import ObjectId
from config import MONGODB_URI, MONGODB_DB_NAME

logger = logging.getLogger(__name__)

class MongoDBService:
    """
    Service for interacting with MongoDB
    """
    def __init__(self):
        try:
            # Connect to MongoDB
            self.client = MongoClient(MONGODB_URI)
            self.db = self.client[MONGODB_DB_NAME]
            
            # Initialize collections
            self.users = self.db.users
            self.stock_data = self.db.stock_data
            self.news_items = self.db.news_items
            self.book_insights = self.db.book_insights
            self.user_queries = self.db.user_queries
            
            logger.info("MongoDB Service initialized successfully")
        except PyMongoError as e:
            logger.error(f"Error initializing MongoDB: {e}")

    # User Operations
    def create_user(self, username, email, password_hash):
        """Create a new user in the database"""
        try:
            user_data = {
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "preferences": {
                    "stock_watchlist": [],
                    "favorite_sectors": [],
                    "risk_profile": "Moderate",
                    "investment_horizon": "Medium Term",
                    "dark_mode": True
                },
                "created_at": datetime.utcnow(),
                "last_login": datetime.utcnow()
            }
            
            result = self.users.insert_one(user_data)
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"Error creating user: {e}")
            return None

    def get_user_by_email(self, email):
        """Retrieve a user by email"""
        try:
            return self.users.find_one({"email": email})
        except PyMongoError as e:
            logger.error(f"Error retrieving user by email: {e}")
            return None

    def update_user_preferences(self, user_id, preferences):
        """Update user preferences"""
        try:
            result = self.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"preferences": preferences}}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Error updating user preferences: {e}")
            return False

    # Stock Data Operations
    def save_stock_data(self, stock_data_dict):
        """Save or update stock data"""
        try:
            # Check if this stock data already exists
            existing = self.stock_data.find_one({
                "symbol": stock_data_dict["symbol"],
                "exchange": stock_data_dict["exchange"]
            })
            
            if existing:
                # Update existing record
                result = self.stock_data.update_one(
                    {"_id": existing["_id"]},
                    {"$set": stock_data_dict}
                )
                return result.modified_count > 0
            else:
                # Insert new record
                result = self.stock_data.insert_one(stock_data_dict)
                return result.inserted_id is not None
        except PyMongoError as e:
            logger.error(f"Error saving stock data: {e}")
            return False

    def get_stock_data(self, symbol, exchange):
        """Retrieve stock data for a specific symbol and exchange"""
        try:
            return self.stock_data.find_one({
                "symbol": symbol,
                "exchange": exchange
            })
        except PyMongoError as e:
            logger.error(f"Error retrieving stock data: {e}")
            return None

    def get_stocks_by_sector(self, sector):
        """Retrieve all stocks in a given sector"""
        try:
            return list(self.stock_data.find({"sector": sector}))
        except PyMongoError as e:
            logger.error(f"Error retrieving stocks by sector: {e}")
            return []

    def get_trending_stocks(self, limit=10):
        """Get trending stocks based on recent performance"""
        try:
            # Get most recent stock data
            all_stocks = list(self.stock_data.find().sort("last_updated", -1).limit(50))
            
            # Sort into gainers and losers
            gainers = [s for s in all_stocks if s.get("day_change", 0) > 0]
            losers = [s for s in all_stocks if s.get("day_change", 0) <= 0]
            
            # Sort by day_change
            gainers.sort(key=lambda x: x.get("day_change", 0), reverse=True)
            losers.sort(key=lambda x: x.get("day_change", 0))
            
            # Return top N of each
            half_limit = limit // 2
            return {
                "gainers": gainers[:half_limit],
                "losers": losers[:half_limit]
            }
        except PyMongoError as e:
            logger.error(f"Error retrieving trending stocks: {e}")
            return {"gainers": [], "losers": []}

    # News Operations
    def save_news_item(self, news_item_dict):
        """Save a news item to the database"""
        try:
            # Check if this news already exists by URL
            existing = self.news_items.find_one({"url": news_item_dict["url"]})
            
            if existing:
                # Update existing record
                result = self.news_items.update_one(
                    {"_id": existing["_id"]},
                    {"$set": news_item_dict}
                )
                return result.modified_count > 0
            else:
                # Insert new record
                result = self.news_items.insert_one(news_item_dict)
                return result.inserted_id is not None
        except PyMongoError as e:
            logger.error(f"Error saving news item: {e}")
            return False

    def get_recent_news(self, limit=20):
        """Retrieve recent news"""
        try:
            return list(self.news_items.find().sort("published_date", -1).limit(limit))
        except PyMongoError as e:
            logger.error(f"Error retrieving recent news: {e}")
            return []

    def get_news_by_stock(self, stock_symbol, limit=10):
        """Retrieve news related to a specific stock"""
        try:
            return list(self.news_items.find(
                {"related_stocks": {"$in": [stock_symbol]}}
            ).sort("published_date", -1).limit(limit))
        except PyMongoError as e:
            logger.error(f"Error retrieving news by stock: {e}")
            return []

    # Book Insights Operations
    def save_book_insight(self, book_insight_dict):
        """Save book insight data"""
        try:
            # Check if this book insight already exists
            existing = self.book_insights.find_one({"book_title": book_insight_dict["book_title"]})
            
            if existing:
                # Update existing record
                result = self.book_insights.update_one(
                    {"_id": existing["_id"]},
                    {"$set": book_insight_dict}
                )
                return result.modified_count > 0
            else:
                # Insert new record
                result = self.book_insights.insert_one(book_insight_dict)
                return result.inserted_id is not None
        except PyMongoError as e:
            logger.error(f"Error saving book insight: {e}")
            return False

    def get_book_insights(self, topic=None):
        """Get book insights, optionally filtered by topic"""
        try:
            if topic:
                return list(self.book_insights.find({"topics": {"$in": [topic]}}))
            else:
                return list(self.book_insights.find())
        except PyMongoError as e:
            logger.error(f"Error retrieving book insights: {e}")
            return []

    # User Query Operations
    def save_user_query(self, user_query_dict):
        """Save a user query and its response"""
        try:
            result = self.user_queries.insert_one(user_query_dict)
            return str(result.inserted_id)
        except PyMongoError as e:
            logger.error(f"Error saving user query: {e}")
            return None

    def get_user_query_history(self, user_id, limit=20):
        """Get query history for a user"""
        try:
            return list(self.user_queries.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(limit))
        except PyMongoError as e:
            logger.error(f"Error retrieving user query history: {e}")
            return []

    def update_query_feedback(self, query_id, feedback):
        """Update feedback for a query"""
        try:
            result = self.user_queries.update_one(
                {"_id": ObjectId(query_id)},
                {"$set": {"feedback": feedback}}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Error updating query feedback: {e}")
            return False

# Create instance of the service
mongodb_service = MongoDBService()
```

## Step 3: Update app.py

Replace the SQLAlchemy setup in `app.py` with MongoDB:

```python
# Replace this code in app.py
from flask import Flask
import os
from config import MONGODB_URI, MONGODB_DB_NAME

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Import services and routes after app is created
from services.db_service import mongodb_service
```

## Step 4: Update Import References

1. Update all imports in service files:

```python
# Change from
from services.db_service import db_service

# To
from services.db_service import mongodb_service
```

2. In each service file, replace calls to `db_service` with `mongodb_service`.

## Step 5: Update User Authentication

For Flask-Login compatibility:

```python
# Create a user loader function in app.py
from flask_login import LoginManager
from bson.objectid import ObjectId

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    # Convert string id to ObjectId
    user_data = mongodb_service.users.find_one({"_id": ObjectId(user_id)})
    if not user_data:
        return None
    
    # Create a User object
    user = User()
    user.id = str(user_data["_id"])
    user.username = user_data["username"]
    user.email = user_data["email"]
    # ... other attributes as needed
    
    return user
```

## Step 6: Update Model Access

Instead of SQLAlchemy models, data is accessed directly through the MongoDB service. Update your code to work with dictionaries rather than model objects.

For example, change:
```python
user = User.query.filter_by(email=email).first()
```

To:
```python
user = mongodb_service.get_user_by_email(email)
```

## Step 7: Data Migration

To migrate existing data from PostgreSQL to MongoDB:

```python
# Create a migration script
def migrate_postgres_to_mongodb():
    # Connect to PostgreSQL
    from app import db, User, StockData, NewsItem, BookInsight, UserQuery
    
    # Connect to MongoDB
    from services.mongodb_service import mongodb_service
    
    # Migrate users
    users = User.query.all()
    for user in users:
        user_dict = {
            "username": user.username,
            "email": user.email,
            "password_hash": user.password_hash,
            "preferences": user.preferences,
            "created_at": user.created_at,
            "last_login": user.last_login
        }
        mongodb_service.users.insert_one(user_dict)
    
    # Migrate stock data
    stocks = StockData.query.all()
    for stock in stocks:
        stock_dict = {
            "symbol": stock.symbol,
            "exchange": stock.exchange,
            "name": stock.name,
            "sector": stock.sector,
            "current_price": stock.current_price,
            "day_change": stock.day_change,
            "volume": stock.volume,
            "high_52week": stock.high_52week,
            "low_52week": stock.low_52week,
            "historical_data": stock.historical_data,
            "last_updated": stock.last_updated
        }
        mongodb_service.stock_data.insert_one(stock_dict)
    
    # Migrate news items, book insights, and user queries similarly
    
    print("Migration completed successfully")
```

## Testing and Verification

1. Test all database operations after migration
2. Verify data integrity between the old and new systems
3. Check authentication flows
4. Test all API endpoints

## Rollback Plan

If any issues occur:

1. Keep the PostgreSQL setup intact while testing MongoDB
2. Create a flag in config to switch between databases
3. Implement a service factory that returns either the SQL or MongoDB service based on the flag

## Performance Considerations

- MongoDB indexes: Create appropriate indexes for frequently queried fields
- Connection pooling: Configure proper connection pooling for production
- Monitoring: Set up MongoDB monitoring to track performance

## Security Considerations

- Use MongoDB Atlas or another secure hosting provider
- Set up proper authentication and RBAC (Role-Based Access Control)
- Enable TLS/SSL for connections
- Use environment variables for all sensitive credentials