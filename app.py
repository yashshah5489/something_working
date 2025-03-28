import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class Base(DeclarativeBase):
    pass

# Create Flask app and configure database
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Use PostgreSQL for database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize SQLAlchemy with the app
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Initialize Flask-Login
from flask_login import LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

with app.app_context():
    # Import models here to ensure they're registered with SQLAlchemy
    import models  # noqa: F401

    # Create all tables in the database
    db.create_all()
    
    # Initialize services that need application context
    from services.rag_service import init_rag_service
    init_rag_service()

# Register learning helper functions
from utils.learning_helpers import register_learning_helpers
register_learning_helpers(app)

# Add custom Jinja filters
from datetime import datetime
@app.template_filter('timestamp_to_datetime')
def timestamp_to_datetime(timestamp):
    """Convert Unix timestamp to formatted datetime string"""
    try:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return "Unknown"

@app.template_filter('nl2br')
def nl2br(text):
    """Convert newlines to HTML line breaks"""
    if not text:
        return ""
    return text.replace('\n', '<br>')

# Register blueprints
from routes.auth_routes import auth_bp
from routes.learning_routes import learning_bp
from routes.main_routes import main_bp
# Import API routes
from routes.api_routes import api_bp

# Register blueprints with the app
app.register_blueprint(auth_bp)
app.register_blueprint(learning_bp)
app.register_blueprint(main_bp)
app.register_blueprint(api_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
