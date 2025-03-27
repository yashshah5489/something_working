from flask import Blueprint, jsonify, request, g
from flask_login import login_required, current_user
import logging
from utils.tavily_api import TavilyNewsExtractor
from utils.groq_api import GroqLLMProcessor
from utils.yahoo_finance_api import YahooFinanceAPI
from utils.rag_processor import RAGProcessor
from utils.langchain_tools import LangChainManager

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

# Initialize API clients
news_client = TavilyNewsExtractor()
llm_client = GroqLLMProcessor()
stock_client = YahooFinanceAPI()
rag_client = RAGProcessor()
langchain_manager = LangChainManager()

@api_bp.route('/news/latest', methods=['GET'])
@login_required
def get_latest_news():
    try:
        limit = request.args.get('limit', 5, type=int)
        market_type = request.args.get('market', 'NSE')
        
        news = news_client.get_latest_market_news(market_type=market_type, limit=limit)
        return jsonify(news)
    except Exception as e:
        logger.error(f"API error in get_latest_news: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/news/search', methods=['GET'])
@login_required
def search_news():
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 10, type=int)
        
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400
        
        news_results = news_client.search_indian_financial_news(query, max_results=limit)
        return jsonify(news_results)
    except Exception as e:
        logger.error(f"API error in search_news: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/stock/data', methods=['GET'])
@login_required
def get_stock_data():
    try:
        symbol = request.args.get('symbol', '')
        period = request.args.get('period', '1mo')
        interval = request.args.get('interval', '1d')
        
        if not symbol:
            return jsonify({"error": "Symbol parameter is required"}), 400
        
        stock_data = stock_client.get_stock_data(symbol, period=period, interval=interval)
        return jsonify(stock_data)
    except Exception as e:
        logger.error(f"API error in get_stock_data: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/stock/multiple', methods=['GET'])
@login_required
def get_multiple_stocks():
    try:
        symbols = request.args.get('symbols', '')
        period = request.args.get('period', '1d')
        interval = request.args.get('interval', '1d')
        
        if not symbols:
            return jsonify({"error": "Symbols parameter is required"}), 400
        
        symbols_list = symbols.split(',')
        stocks_data = stock_client.get_multiple_stocks(symbols_list, period=period, interval=interval)
        return jsonify(stocks_data)
    except Exception as e:
        logger.error(f"API error in get_multiple_stocks: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/market/summary', methods=['GET'])
@login_required
def get_market_summary():
    try:
        indices = request.args.get('indices')
        if indices:
            indices = indices.split(',')
        
        market_summary = stock_client.get_market_summary(indices=indices)
        return jsonify(market_summary)
    except Exception as e:
        logger.error(f"API error in get_market_summary: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/sectors/performance', methods=['GET'])
@login_required
def get_sector_performance():
    try:
        sectors = request.args.get('sectors')
        if sectors:
            sectors = sectors.split(',')
        
        sector_performance = stock_client.get_sector_performance(sectors=sectors)
        return jsonify(sector_performance)
    except Exception as e:
        logger.error(f"API error in get_sector_performance: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/llm/analyze_stock', methods=['POST'])
@login_required
def analyze_stock():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        symbol = data.get('symbol')
        stock_data = data.get('stock_data')
        additional_context = data.get('additional_context')
        
        if not symbol or not stock_data:
            return jsonify({"error": "Symbol and stock_data are required"}), 400
        
        analysis = llm_client.analyze_stock(stock_data, symbol, additional_context)
        return jsonify(analysis)
    except Exception as e:
        logger.error(f"API error in analyze_stock: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/llm/interpret_news', methods=['POST'])
@login_required
def interpret_news():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        news_data = data.get('news_data')
        stock_symbols = data.get('stock_symbols')
        
        if not news_data:
            return jsonify({"error": "news_data is required"}), 400
        
        interpretation = llm_client.interpret_news_impact(news_data, stock_symbols)
        return jsonify(interpretation)
    except Exception as e:
        logger.error(f"API error in interpret_news: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/llm/financial_concept', methods=['GET'])
@login_required
def explain_financial_concept():
    try:
        concept = request.args.get('concept', '')
        
        if not concept:
            return jsonify({"error": "Concept parameter is required"}), 400
        
        explanation = llm_client.explain_financial_concept(concept)
        return jsonify(explanation)
    except Exception as e:
        logger.error(f"API error in explain_financial_concept: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/llm/tax_advice', methods=['GET'])
@login_required
def get_tax_advice():
    try:
        investment_type = request.args.get('investment_type', '')
        holding_period = request.args.get('holding_period')
        income_bracket = request.args.get('income_bracket')
        
        if not investment_type:
            return jsonify({"error": "investment_type parameter is required"}), 400
        
        advice = llm_client.get_tax_advice(investment_type, holding_period, income_bracket)
        return jsonify(advice)
    except Exception as e:
        logger.error(f"API error in get_tax_advice: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/books/recommendations', methods=['GET'])
@login_required
def get_book_recommendations():
    try:
        goal = request.args.get('goal', '')
        
        if not goal:
            return jsonify({"error": "Financial goal parameter is required"}), 400
        
        recommendations = rag_client.get_book_recommendations(goal)
        return jsonify(recommendations)
    except Exception as e:
        logger.error(f"API error in get_book_recommendations: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/books/advice', methods=['POST'])
@login_required
def get_book_advice():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        question = data.get('question')
        context = data.get('context')
        
        if not question:
            return jsonify({"error": "Question is required"}), 400
        
        advice = rag_client.get_financial_advice_from_books(question, context)
        return jsonify(advice)
    except Exception as e:
        logger.error(f"API error in get_book_advice: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/watchlist/update', methods=['POST'])
@login_required
def update_watchlist():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        symbol = data.get('symbol')
        action = data.get('action')  # 'add' or 'remove'
        
        if not symbol or not action:
            return jsonify({"error": "Symbol and action are required"}), 400
        
        db = g.db
        
        if action == 'add':
            if symbol not in current_user.watchlist:
                db.users.update_one(
                    {'_id': current_user.id},
                    {'$push': {'watchlist': symbol}}
                )
                current_user.watchlist.append(symbol)
                result = {"status": "added", "symbol": symbol}
            else:
                result = {"status": "already_exists", "symbol": symbol}
        elif action == 'remove':
            db.users.update_one(
                {'_id': current_user.id},
                {'$pull': {'watchlist': symbol}}
            )
            if symbol in current_user.watchlist:
                current_user.watchlist.remove(symbol)
            result = {"status": "removed", "symbol": symbol}
        else:
            return jsonify({"error": "Invalid action"}), 400
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"API error in update_watchlist: {e}")
        return jsonify({"error": str(e)}), 500

# Set up database reference
@api_bp.before_request
def before_request():
    from app import db
    g.db = db
