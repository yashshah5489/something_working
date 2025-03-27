from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify
from flask_login import login_required, current_user
import logging
from datetime import datetime
from utils.tavily_api import TavilyNewsExtractor
from utils.groq_api import GroqLLMProcessor
from utils.yahoo_finance_api import YahooFinanceAPI
from utils.rag_processor import RAGProcessor
from utils.langchain_tools import LangChainManager
from config import DEFAULT_STOCKS

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

# Initialize API clients
news_client = TavilyNewsExtractor()
llm_client = GroqLLMProcessor()
stock_client = YahooFinanceAPI()
rag_client = RAGProcessor()
langchain_manager = LangChainManager()

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    try:
        # Get market summary
        market_summary = stock_client.get_market_summary()
        
        # Get latest news
        latest_news = news_client.get_latest_market_news(limit=5)
        
        # Get user's watchlist stocks
        watchlist_symbols = current_user.watchlist
        watchlist_data = {}
        if watchlist_symbols:
            watchlist_data = stock_client.get_multiple_stocks(watchlist_symbols, period="1d")
        
        # Get sector performance
        sector_performance = stock_client.get_sector_performance()
        
        return render_template(
            'dashboard.html',
            market_summary=market_summary,
            latest_news=latest_news,
            watchlist_data=watchlist_data,
            sector_performance=sector_performance
        )
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash('An error occurred while loading the dashboard', 'danger')
        return render_template('dashboard.html')

@main_bp.route('/stocks')
@login_required
def stocks():
    """Stocks overview page route"""
    try:
        # Get query parameters
        symbol = request.args.get('symbol', 'NIFTY50')
        exchange = request.args.get('exchange', 'NSE')
        
        # Redirect to stock detail page
        return redirect(url_for('main.stock_detail', symbol=symbol))
        
    except Exception as e:
        logger.error(f"Error loading stocks page: {e}")
        flash("An error occurred while loading the stocks page", 'danger')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/stock/<symbol>')
@login_required
def stock_detail(symbol):
    try:
        # Get stock data
        stock_data = stock_client.get_stock_data(symbol, period="6mo")
        
        # Get recent news about the stock
        company_name = stock_data.get('info', {}).get('shortName', symbol)
        stock_news = news_client.get_company_news(company_name, limit=5)
        
        # Get stock analysis from LLM
        stock_analysis = llm_client.analyze_stock(stock_data, symbol)
        
        # Check if stock is in user's watchlist
        in_watchlist = symbol in current_user.watchlist
        
        return render_template(
            'stock_analysis.html',
            stock_data=stock_data,
            stock_news=stock_news,
            stock_analysis=stock_analysis,
            in_watchlist=in_watchlist
        )
        
    except Exception as e:
        logger.error(f"Error loading stock detail for {symbol}: {e}")
        flash(f'An error occurred while loading data for {symbol}', 'danger')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/watchlist/add/<symbol>', methods=['POST'])
@login_required
def add_to_watchlist(symbol):
    try:
        db = g.db
        
        # Check if already in watchlist
        if symbol in current_user.watchlist:
            flash(f'{symbol} is already in your watchlist', 'info')
        else:
            # Add to watchlist
            db.users.update_one(
                {'_id': current_user.id},
                {'$push': {'watchlist': symbol}}
            )
            current_user.watchlist.append(symbol)
            flash(f'{symbol} added to your watchlist', 'success')
        
        # Return to stock page
        return redirect(url_for('main.stock_detail', symbol=symbol))
        
    except Exception as e:
        logger.error(f"Error adding {symbol} to watchlist: {e}")
        flash('An error occurred', 'danger')
        return redirect(url_for('main.stock_detail', symbol=symbol))

@main_bp.route('/watchlist/remove/<symbol>', methods=['POST'])
@login_required
def remove_from_watchlist(symbol):
    try:
        db = g.db
        
        # Remove from watchlist
        db.users.update_one(
            {'_id': current_user.id},
            {'$pull': {'watchlist': symbol}}
        )
        
        if symbol in current_user.watchlist:
            current_user.watchlist.remove(symbol)
        
        flash(f'{symbol} removed from your watchlist', 'success')
        
        # Check if request is from watchlist page
        referrer = request.referrer
        if referrer and 'watchlist' in referrer:
            return redirect(url_for('main.watchlist'))
        
        # Return to stock page
        return redirect(url_for('main.stock_detail', symbol=symbol))
        
    except Exception as e:
        logger.error(f"Error removing {symbol} from watchlist: {e}")
        flash('An error occurred', 'danger')
        return redirect(url_for('main.stock_detail', symbol=symbol))

@main_bp.route('/watchlist')
@login_required
def watchlist():
    try:
        watchlist_symbols = current_user.watchlist
        
        if not watchlist_symbols:
            # Show empty watchlist template
            return render_template(
                'watchlist.html',
                watchlist_data=None,
                default_stocks=DEFAULT_STOCKS
            )
        
        # Get data for watchlist stocks
        watchlist_data = stock_client.get_multiple_stocks(watchlist_symbols)
        
        return render_template(
            'watchlist.html',
            watchlist_data=watchlist_data
        )
        
    except Exception as e:
        logger.error(f"Error loading watchlist: {e}")
        flash('An error occurred while loading your watchlist', 'danger')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/news')
@login_required
def news():
    try:
        # Get latest market news
        market_news = news_client.get_latest_market_news(limit=10)
        
        # Get policy updates
        policy_updates = news_client.get_policy_updates(limit=5)
        
        # Get sector-specific news if sector parameter is provided
        sector = request.args.get('sector')
        sector_news = None
        if sector:
            sector_news = news_client.get_sector_news(sector, limit=5)
        
        return render_template(
            'news.html',
            market_news=market_news,
            policy_updates=policy_updates,
            sector_news=sector_news,
            sector=sector
        )
        
    except Exception as e:
        logger.error(f"Error loading news: {e}")
        flash('An error occurred while loading news', 'danger')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    
    if not query:
        return redirect(url_for('main.dashboard'))
    
    try:
        # Search for stocks
        stock_results = stock_client.search_stocks(query)
        
        # Search for news
        news_results = news_client.search_indian_financial_news(query)
        
        return render_template(
            'search_results.html',
            query=query,
            stock_results=stock_results,
            news_results=news_results
        )
        
    except Exception as e:
        logger.error(f"Error in search for query '{query}': {e}")
        flash('An error occurred while processing your search', 'danger')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/insights')
@login_required
def insights():
    """Alias route for financial-insights for backward compatibility"""
    return redirect(url_for('main.financial_insights'))

@main_bp.route('/financial-insights', methods=['GET', 'POST'])
@login_required
def financial_insights():
    if request.method == 'POST':
        question = request.form.get('question')
        
        if not question:
            flash('Please enter a question', 'danger')
            return redirect(url_for('main.financial_insights'))
        
        try:
            # Get market data for context
            market_data = stock_client.get_market_summary()
            
            # Get recent news for context
            news_data = news_client.get_latest_market_news(limit=5)
            
            # Create context
            context = {
                "market_summary": market_data,
                "recent_news": news_data
            }
            
            # Get insights from LLM
            insights = llm_client.get_financial_insights(context, question)
            
            # Get relevant book insights
            book_advice = rag_client.get_financial_advice_from_books(question, context)
            
            return render_template(
                'financial_insights.html',
                question=question,
                insights=insights,
                book_advice=book_advice
            )
            
        except Exception as e:
            logger.error(f"Error getting financial insights: {e}")
            flash('An error occurred while processing your question', 'danger')
            return render_template('financial_insights.html')
    
    # GET request
    # Suggest some common financial questions
    suggested_questions = [
        "What are the best tax-saving investment options in India?",
        "How should I allocate my investments across mutual funds, stocks, and fixed income?",
        "What are the implications of the latest RBI policy on my investments?",
        "How does LTCG tax work for equity investments in India?",
        "Should I invest in an NPS account for retirement?",
        "What's a good strategy for SIP investments in the current market?"
    ]
    
    return render_template(
        'financial_insights.html',
        suggested_questions=suggested_questions
    )

@main_bp.route('/books')
@login_required
def books():
    """Alias route for book-recommendations for backward compatibility"""
    return redirect(url_for('main.book_recommendations'))

@main_bp.route('/book-recommendations')
@login_required
def book_recommendations():
    try:
        # Get default book recommendations
        default_recommendations = rag_client.financial_books
        
        # Get personalized recommendations if goal is provided
        goal = request.args.get('goal')
        personalized_recommendations = None
        
        if goal:
            personalized_recommendations = rag_client.get_book_recommendations(goal)
        
        return render_template(
            'book_recommendations.html',
            default_recommendations=default_recommendations,
            personalized_recommendations=personalized_recommendations,
            goal=goal
        )
        
    except Exception as e:
        logger.error(f"Error getting book recommendations: {e}")
        flash('An error occurred while loading book recommendations', 'danger')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/tax-advisor', methods=['GET', 'POST'])
@login_required
def tax_advisor():
    if request.method == 'POST':
        question = request.form.get('question')
        investment_type = request.form.get('investment_type')
        holding_period = request.form.get('holding_period')
        income_bracket = request.form.get('income_bracket')
        
        try:
            # Get tax advice
            tax_advice = llm_client.get_tax_advice(
                investment_type=investment_type,
                holding_period=holding_period,
                income_bracket=income_bracket
            )
            
            return render_template(
                'tax_advisor.html',
                investment_type=investment_type,
                holding_period=holding_period,
                income_bracket=income_bracket,
                tax_advice=tax_advice
            )
            
        except Exception as e:
            logger.error(f"Error getting tax advice: {e}")
            flash('An error occurred while processing your tax query', 'danger')
            return render_template('tax_advisor.html')
    
    # GET request
    investment_types = [
        "Equity Shares",
        "Mutual Funds",
        "Fixed Deposits",
        "Real Estate",
        "Gold",
        "ELSS",
        "PPF",
        "NPS"
    ]
    
    holding_periods = [
        "Less than 1 year",
        "1-3 years",
        "More than 3 years"
    ]
    
    income_brackets = [
        "Up to ₹2.5 Lakh",
        "₹2.5 Lakh - ₹5 Lakh",
        "₹5 Lakh - ₹10 Lakh",
        "₹10 Lakh - ₹50 Lakh",
        "Above ₹50 Lakh"
    ]
    
    return render_template(
        'tax_advisor.html',
        investment_types=investment_types,
        holding_periods=holding_periods,
        income_brackets=income_brackets
    )

# Set up database reference
@main_bp.before_request
def before_request():
    from app import db
    g.db = db
