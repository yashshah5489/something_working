import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from services.news_service import news_service
from services.stock_service import stock_service
from services.llm_service import llm_service
from services.rag_service import rag_service, init_rag_service
from services.db_service import db_service
from config import FINANCIAL_BOOKS, INDIAN_STOCK_EXCHANGES

logger = logging.getLogger(__name__)

# Main routes
@app.route('/')
def index():
    """Home page route"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard page route"""
    try:
        # Get trending stocks
        trending_stocks = stock_service.get_trending_stocks(limit=10)
        
        # Get recent news
        recent_news = db_service.get_recent_news(limit=5)
        
        # Get sector performance
        sector_performance = stock_service.get_sector_performance()
        
        # Get latest market news using Yahoo Finance
        regulatory_updates = stock_service.get_stock_news(max_results=3)
        
        return render_template(
            'dashboard.html',
            trending_gainers=trending_stocks.get("gainers", []),
            trending_losers=trending_stocks.get("losers", []),
            recent_news=recent_news,
            sector_performance=sector_performance,
            regulatory_updates=regulatory_updates
        )
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash("An error occurred while loading the dashboard. Please try again later.", "error")
        return render_template('dashboard.html', error=True)

@app.route('/news')
def news():
    """News page route"""
    try:
        # Get query parameter for news type
        news_type = request.args.get('type', 'all')
        
        # Use Yahoo Finance for all news categories
        if news_type == 'regulatory':
            # For regulatory news, we'll use general market news but filter by keywords
            news_items = stock_service.get_stock_news(max_results=10)
            # Filter for potential regulatory content using keywords
            news_items = [item for item in news_items if any(
                keyword in item.get('title', '').lower() + ' ' + item.get('summary', '').lower() 
                for keyword in ['rbi', 'sebi', 'policy', 'regulation', 'regulator', 'guidelines'])]
            analysis_title = "Regulatory Update Analysis"
        elif news_type == 'budget':
            # For budget news, we'll use general market news but filter by keywords
            news_items = stock_service.get_stock_news(max_results=10)
            # Filter for potential budget-related content using keywords
            news_items = [item for item in news_items if any(
                keyword in item.get('title', '').lower() + ' ' + item.get('summary', '').lower() 
                for keyword in ['budget', 'fiscal', 'tax', 'finance ministry', 'economic policy', 'government'])]
            analysis_title = "Budget & Economic Policy Analysis"
        else:  # 'all' or any other value
            news_items = stock_service.get_stock_news(max_results=15)
            analysis_title = "Financial News Analysis"
        
        # Get news analysis
        if news_items:
            news_analysis = llm_service.analyze_news(news_items[:5])
        else:
            news_analysis = "No news to analyze at this time."
        
        return render_template(
            'news.html',
            news_items=news_items,
            news_type=news_type,
            news_analysis=news_analysis,
            analysis_title=analysis_title
        )
    except Exception as e:
        logger.error(f"Error loading news page: {e}")
        flash("An error occurred while loading the news. Please try again later.", "error")
        return render_template('news.html', error=True)

@app.route('/stocks')
def stocks():
    """Stocks page route"""
    try:
        # Get query parameters
        symbol = request.args.get('symbol', 'RELIANCE')
        exchange = request.args.get('exchange', 'NSE')
        
        # Get stock data
        stock_data = stock_service.get_stock_data(symbol, exchange)
        
        # Get stock historical data (for chart)
        historical_data = stock_service.get_historical_data(symbol, exchange, period="1mo")
        
        # Get stock-specific news using Yahoo Finance
        stock_news = stock_service.get_stock_news(symbol, exchange, max_results=5)
        
        # Get stock analysis from LLM
        if stock_data:
            stock_analysis = llm_service.analyze_stock(stock_data, stock_news)
        else:
            stock_analysis = f"Unable to analyze {symbol} at this time."
        
        # Get trending stocks for sidebar
        trending_stocks = stock_service.get_trending_stocks(limit=10)
        
        return render_template(
            'stocks.html',
            stock_data=stock_data,
            historical_data=historical_data,
            stock_news=stock_news,
            stock_analysis=stock_analysis,
            trending_gainers=trending_stocks.get("gainers", []),
            trending_losers=trending_stocks.get("losers", []),
            exchanges=INDIAN_STOCK_EXCHANGES,
            selected_symbol=symbol,
            selected_exchange=exchange
        )
    except Exception as e:
        logger.error(f"Error loading stocks page: {e}")
        flash("An error occurred while loading the stock information. Please try again later.", "error")
        return render_template('stocks.html', error=True)

@app.route('/insights')
def insights():
    """Financial insights page route"""
    try:
        # Get query from request
        query = request.args.get('query', '')
        
        # Default insights if no query
        if not query:
            return render_template(
                'insights.html',
                query='',
                answer='',
                book_recommendations=[]
            )
        
        # Get answer from LLM
        answer = llm_service.answer_financial_question(query)
        
        # Ensure rag_service is initialized
        if rag_service is None:
            init_rag_service()
            logger.info("RAG service initialized on demand")
        
        # Get related book recommendations
        book_recommendations = rag_service.get_book_recommendations(query)
        
        # Enhance the answer with book insights
        enhanced_answer = rag_service.enhance_llm_response(query, answer)
        
        return render_template(
            'insights.html',
            query=query,
            answer=enhanced_answer,
            book_recommendations=book_recommendations
        )
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        flash("An error occurred while generating insights. Please try again later.", "error")
        return render_template('insights.html', error=True)

@app.route('/books')
def books():
    """Financial books page route"""
    try:
        # Get topic and goal from request
        topic = request.args.get('topic', '')
        goal = request.args.get('goal', '')
        
        # Default empty state if no topic/goal
        if not topic or not goal:
            return render_template(
                'books.html',
                topic='',
                goal='',
                recommendations='',
                available_books=FINANCIAL_BOOKS
            )
        
        # Get book recommendations
        recommendations = llm_service.recommend_books(topic, goal, FINANCIAL_BOOKS)
        
        return render_template(
            'books.html',
            topic=topic,
            goal=goal,
            recommendations=recommendations,
            available_books=FINANCIAL_BOOKS
        )
    except Exception as e:
        logger.error(f"Error loading books page: {e}")
        flash("An error occurred while loading the books recommendations. Please try again later.", "error")
        return render_template('books.html', error=True)

# API routes
@app.route('/api/stocks/search', methods=['GET'])
def search_stocks_api():
    """API endpoint to search for stocks"""
    try:
        query = request.args.get('query', '').strip()
        if not query or len(query) < 2:
            return jsonify({
                'success': False,
                'error': 'Search query must be at least 2 characters'
            }), 400
            
        # This is a simplified search - in production, this would be much more sophisticated
        # and connect to a stock market API for real-time data
        results = []
        
        # Common Indian stocks for demo purposes
        common_stocks = [
            {"symbol": "RELIANCE", "name": "Reliance Industries", "exchange": "NSE"},
            {"symbol": "TCS", "name": "Tata Consultancy Services", "exchange": "NSE"},
            {"symbol": "HDFCBANK", "name": "HDFC Bank", "exchange": "NSE"},
            {"symbol": "INFY", "name": "Infosys", "exchange": "NSE"},
            {"symbol": "BAJFINANCE", "name": "Bajaj Finance", "exchange": "NSE"},
            {"symbol": "HINDUNILVR", "name": "Hindustan Unilever", "exchange": "NSE"},
            {"symbol": "SBIN", "name": "State Bank of India", "exchange": "NSE"},
            {"symbol": "BHARTIARTL", "name": "Bharti Airtel", "exchange": "NSE"},
            {"symbol": "ICICIBANK", "name": "ICICI Bank", "exchange": "NSE"},
            {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank", "exchange": "NSE"},
            {"symbol": "ADANIPORTS", "name": "Adani Ports", "exchange": "NSE"},
            {"symbol": "WIPRO", "name": "Wipro", "exchange": "NSE"},
            {"symbol": "ASIANPAINT", "name": "Asian Paints", "exchange": "NSE"},
            {"symbol": "ITC", "name": "ITC", "exchange": "NSE"},
            {"symbol": "AXISBANK", "name": "Axis Bank", "exchange": "NSE"}
        ]
        
        # Filter stocks based on query
        query_lower = query.lower()
        for stock in common_stocks:
            if (query_lower in stock["symbol"].lower() or 
                query_lower in stock["name"].lower()):
                results.append(stock)
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        logger.error(f"Error searching stocks: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/news/refresh', methods=['POST'])
def refresh_news():
    """API endpoint to refresh news data using Yahoo Finance instead of Tavily"""
    try:
        data = request.get_json()
        news_type = data.get('type', 'all') if data else 'all'
        symbol = data.get('symbol') if data else None
        exchange = data.get('exchange') if data else None
        max_results = int(data.get('max_results', 10)) if data else 10
        
        # Use Yahoo Finance through the stock service to get news
        if news_type == 'stock' and symbol:
            # Get news for specific stock
            news_items = stock_service.get_stock_news(symbol, exchange, max_results)
            message = f'Fetched news for {symbol} ({len(news_items)} items)'
        else:  # 'all' or any other value
            # Get general market news
            news_items = stock_service.get_stock_news(max_results=max_results)
            message = f'Fetched general market news ({len(news_items)} items)'
        
        # Convert datetime objects to strings for JSON serialization
        for item in news_items:
            if 'published_date' in item and hasattr(item['published_date'], 'isoformat'):
                item['published_date'] = item['published_date'].isoformat()
        
        return jsonify({
            'success': True,
            'message': message,
            'news_items': news_items
        })
    except Exception as e:
        logger.error(f"Error refreshing news: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stocks/data', methods=['GET'])
def get_stock_data_api():
    """API endpoint to get stock data"""
    try:
        symbol = request.args.get('symbol', 'RELIANCE')
        exchange = request.args.get('exchange', 'NSE')
        
        stock_data = stock_service.get_stock_data(symbol, exchange)
        
        if not stock_data:
            return jsonify({
                'success': False,
                'error': f"No data found for {symbol} on {exchange}"
            }), 404
        
        # Convert datetime objects to strings for JSON serialization
        if 'last_updated' in stock_data and hasattr(stock_data['last_updated'], 'isoformat'):
            stock_data['last_updated'] = stock_data['last_updated'].isoformat()
        
        return jsonify({
            'success': True,
            'stock_data': stock_data
        })
    except Exception as e:
        logger.error(f"Error getting stock data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stocks/historical', methods=['GET'])
def get_historical_data_api():
    """API endpoint to get historical stock data"""
    try:
        symbol = request.args.get('symbol', 'RELIANCE')
        exchange = request.args.get('exchange', 'NSE')
        period = request.args.get('period', '1mo')
        
        historical_data = stock_service.get_historical_data(symbol, exchange, period)
        
        return jsonify({
            'success': True,
            'historical_data': historical_data
        })
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/insights/question', methods=['POST'])
def answer_question_api():
    """API endpoint to answer a financial question"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'No query provided'
            }), 400
        
        # Get answer from LLM
        answer = llm_service.answer_financial_question(query)
        
        # Get related book recommendations
        book_recommendations = rag_service.get_book_recommendations(query)
        
        # Enhance the answer with book insights
        enhanced_answer = rag_service.enhance_llm_response(query, answer)
        
        return jsonify({
            'success': True,
            'query': query,
            'answer': enhanced_answer,
            'book_recommendations': book_recommendations
        })
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/market/summary', methods=['GET'])
def market_summary_api():
    """API endpoint to get market summary"""
    try:
        # Get sector performance data
        sector_performance = stock_service.get_sector_performance()
        
        # Get trending stocks
        trending_stocks = stock_service.get_trending_stocks(limit=5)
        
        # Get key market indices
        indices = [
            {"symbol": "NIFTY50", "exchange": "NSE"},
            {"symbol": "BANKNIFTY", "exchange": "NSE"},
            {"symbol": "NIFTYMIDCAP", "exchange": "NSE"},
            {"symbol": "SENSEX", "exchange": "BSE"}
        ]
        
        indices_data = []
        for index in indices:
            try:
                data = stock_service.get_stock_data(index["symbol"], index["exchange"])
                if data:
                    indices_data.append(data)
            except Exception as e:
                logger.warning(f"Could not fetch data for {index['symbol']}: {e}")
        
        # Recent news headlines using Yahoo Finance instead of Tavily
        recent_news = stock_service.get_stock_news(max_results=3)
        news_headlines = []
        for news in recent_news:
            if "title" in news and "url" in news:
                news_headlines.append({
                    "title": news["title"],
                    "url": news["url"],
                    "source": news.get("source", "Yahoo Finance")
                })
        
        return jsonify({
            'success': True,
            'market_data': {
                'sector_performance': sector_performance,
                'trending_gainers': trending_stocks.get("gainers", []),
                'trending_losers': trending_stocks.get("losers", []),
                'indices': indices_data,
                'news_headlines': news_headlines
            }
        })
    except Exception as e:
        logger.error(f"Error getting market summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/books/recommend', methods=['POST'])
def recommend_books_api():
    """API endpoint to recommend books"""
    try:
        data = request.get_json()
        topic = data.get('topic', '')
        goal = data.get('goal', '')
        
        if not topic or not goal:
            return jsonify({
                'success': False,
                'error': 'Topic and goal are required'
            }), 400
        
        # Get book recommendations
        recommendations = llm_service.recommend_books(topic, goal, FINANCIAL_BOOKS)
        
        return jsonify({
            'success': True,
            'topic': topic,
            'goal': goal,
            'recommendations': recommendations
        })
    except Exception as e:
        logger.error(f"Error recommending books: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Route at line 455 is a duplicate and was removed

@app.route('/api/user/preferences', methods=['GET', 'POST'])
def user_preferences_api():
    """API endpoint to get/update user preferences"""
    try:
        # This would normally use the current logged-in user's ID
        # For simplicity, we'll use a default user ID
        user_id = 1  
        
        # GET request - retrieve preferences
        if request.method == 'GET':
            user = db_service.get_user_by_id(user_id)
            
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'User not found'
                }), 404
                
            # Convert preferences to JSON-safe format
            preferences = {}
            if hasattr(user, 'preferences') and user.preferences:
                preferences = user.preferences
            elif isinstance(user, dict) and 'preferences' in user:
                preferences = user['preferences']
            
            return jsonify({
                'success': True,
                'preferences': preferences
            })
        
        # POST request - update preferences
        elif request.method == 'POST':
            data = request.get_json()
            preferences = data.get('preferences', {})
            
            if not preferences:
                return jsonify({
                    'success': False,
                    'error': 'No preferences provided'
                }), 400
                
            # Update user preferences
            result = db_service.update_user_preferences(user_id, preferences)
            
            if not result:
                return jsonify({
                    'success': False,
                    'error': 'Failed to update preferences'
                }), 500
                
            return jsonify({
                'success': True,
                'message': 'Preferences updated successfully',
                'preferences': preferences
            })
            
    except Exception as e:
        logger.error(f"Error managing user preferences: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('index.html', error="Internal server error"), 500
