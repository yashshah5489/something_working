import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from services.news_service import news_service
from services.stock_service import stock_service
from services.llm_service import llm_service
from services.rag_service import rag_service
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
        
        # Get latest RBI/SEBI updates
        regulatory_updates = news_service.get_rbi_sebi_updates(max_results=3)
        
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
        
        if news_type == 'regulatory':
            news_items = news_service.get_rbi_sebi_updates(max_results=10)
            analysis_title = "Regulatory Update Analysis"
        elif news_type == 'budget':
            news_items = news_service.get_budget_economic_news(max_results=10)
            analysis_title = "Budget & Economic Policy Analysis"
        else:  # 'all' or any other value
            news_items = news_service.get_financial_news(max_results=15)
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
        
        # Get stock-specific news
        stock_news = news_service.get_stock_specific_news(symbol, exchange)
        
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
@app.route('/api/news/refresh', methods=['POST'])
def refresh_news():
    """API endpoint to refresh news data"""
    try:
        news_type = request.json.get('type', 'all')
        
        if news_type == 'regulatory':
            news_items = news_service.get_rbi_sebi_updates(max_results=10)
        elif news_type == 'budget':
            news_items = news_service.get_budget_economic_news(max_results=10)
        else:  # 'all' or any other value
            news_items = news_service.get_financial_news(max_results=15)
        
        # Convert datetime objects to strings for JSON serialization
        for item in news_items:
            if 'published_date' in item and hasattr(item['published_date'], 'isoformat'):
                item['published_date'] = item['published_date'].isoformat()
        
        return jsonify({
            'success': True,
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

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('index.html', error="Internal server error"), 500
