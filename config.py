import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# MongoDB Configuration
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/finance_analyzer")
MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "finance_analyzer")

# API Keys
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL_NAME = "llama3-70b-8192"

# India-specific constants
INDIAN_STOCK_EXCHANGES = ["NSE", "BSE"]
DEFAULT_STOCK_EXCHANGE = "NSE"

# Default stocks for recommendation (keeping as historical reference)
DEFAULT_STOCKS = [
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "exchange": "NSE"},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "exchange": "NSE"},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "exchange": "NSE"},
    {"symbol": "INFY.NS", "name": "Infosys", "exchange": "NSE"},
    {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever", "exchange": "NSE"},
    {"symbol": "ITC.NS", "name": "ITC", "exchange": "NSE"},
    {"symbol": "SBIN.NS", "name": "State Bank of India", "exchange": "NSE"},
    {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel", "exchange": "NSE"},
    {"symbol": "BAJFINANCE.NS", "name": "Bajaj Finance", "exchange": "NSE"},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank", "exchange": "NSE"}
]

# Indian Market Indices (Main focus of the application)
INDIAN_MARKET_INDICES = [
    {"symbol": "^NSEI", "name": "Nifty 50", "description": "Benchmark index representing the weighted average of 50 of the largest Indian companies listed on NSE", "category": "Broad Market"},
    {"symbol": "^BSESN", "name": "BSE Sensex", "description": "Benchmark index of 30 well-established and financially sound companies listed on BSE", "category": "Broad Market"},
    {"symbol": "NIFTY BANK.NS", "name": "Nifty Bank", "description": "Index of the most liquid and large Indian banking stocks", "category": "Sector"},
    {"symbol": "NIFTY IT.NS", "name": "Nifty IT", "description": "Index tracking performance of IT companies listed on NSE", "category": "Sector"},
    {"symbol": "NIFTY PHARMA.NS", "name": "Nifty Pharma", "description": "Index tracking performance of pharmaceutical companies", "category": "Sector"},
    {"symbol": "NIFTY AUTO.NS", "name": "Nifty Auto", "description": "Index tracking auto and auto component companies", "category": "Sector"},
    {"symbol": "NIFTY FMCG.NS", "name": "Nifty FMCG", "description": "Index tracking companies in the fast-moving consumer goods sector", "category": "Sector"},
    {"symbol": "NIFTY METAL.NS", "name": "Nifty Metal", "description": "Index tracking companies in the metals sector", "category": "Sector"},
    {"symbol": "NIFTY REALTY.NS", "name": "Nifty Realty", "description": "Index tracking real estate companies", "category": "Sector"},
    {"symbol": "NIFTY ENERGY.NS", "name": "Nifty Energy", "description": "Index tracking energy sector companies", "category": "Sector"},
    {"symbol": "^NSMIDCP", "name": "Nifty Midcap 100", "description": "Index representing the midcap segment of the market", "category": "Market Cap"},
    {"symbol": "^NSEMDCP50", "name": "Nifty Midcap 50", "description": "Index of the top 50 midcap companies", "category": "Market Cap"},
    {"symbol": "^CNXSMCAP", "name": "Nifty Smallcap 100", "description": "Index representing the smallcap segment of the market", "category": "Market Cap"},
    {"symbol": "NIFTY DIV OPPS 50.NS", "name": "Nifty Dividend Opportunities 50", "description": "Index tracking high dividend yield companies", "category": "Strategy"},
    {"symbol": "NIFTY100 LOWVOL30.NS", "name": "Nifty100 Low Volatility 30", "description": "Index tracking low volatility companies from Nifty 100", "category": "Strategy"},
    {"symbol": "NIFTY100 QUAL30.NS", "name": "Nifty100 Quality 30", "description": "Index tracking high quality companies from Nifty 100", "category": "Strategy"}
]

# News sources for India
INDIAN_NEWS_SOURCES = [
    "Economic Times",
    "Business Standard",
    "Mint",
    "Financial Express",
    "Moneycontrol",
    "LiveMint",
    "NDTV Profit",
    "Bloomberg Quint"
]

# Financial news sources for Tavily API
FINANCIAL_NEWS_SOURCES = [
    "economictimes.indiatimes.com",
    "moneycontrol.com",
    "business-standard.com",
    "financialexpress.com",
    "livemint.com",
    "businesstoday.in",
    "cnbctv18.com",
    "bloombergquint.com",
    "rbi.org.in",
    "sebi.gov.in"
]

# Popular Indian financial books for RAG
FINANCIAL_BOOKS = [
    {"title": "Let's Talk Money", "author": "Monika Halan", "category": "Personal Finance"},
    {"title": "The Intelligent Investor", "author": "Benjamin Graham", "category": "Value Investing"},
    {"title": "Rich Dad Poor Dad", "author": "Robert Kiyosaki", "category": "Financial Mindset"},
    {"title": "Bulls, Bears and Other Beasts", "author": "Santosh Nair", "category": "Indian Markets"},
    {"title": "I Do What I Do", "author": "Raghuram Rajan", "category": "Economy"},
    {"title": "Financial Intelligence", "author": "Karen Berman", "category": "Financial Literacy"},
    {"title": "The 5 Mistakes Every Investor Makes", "author": "Peter Mallouk", "category": "Investment Mistakes"},
    {"title": "Value Investing and Behavioral Finance", "author": "Parag Parikh", "category": "Value Investing"}
]

# LLM Templates
STOCK_ANALYSIS_TEMPLATE = """
Analyze the following stock data for {stock_symbol} from {exchange}:
Price: {price}
Change: {change}
Volume: {volume}
52-week High: {high_52week}
52-week Low: {low_52week}

Based on recent news: {news_summary}

Provide a comprehensive analysis including:
1. Current performance assessment
2. Potential India-specific factors affecting this stock
3. Short-term and long-term outlook
4. Risk assessment (High/Medium/Low)
5. Investment recommendation for Indian investors

Keep in mind Indian taxation policies, SEBI regulations, and market conditions.
"""

NEWS_ANALYSIS_TEMPLATE = """
Analyze the following financial news from India:
{news_items}

Provide insights on:
1. Key market trends
2. Potential impact on different sectors of the Indian economy
3. Implications for retail investors in India
4. Recommended actions or areas to monitor
5. Any regulatory changes and their effects

Include relevant context about Indian financial policies, taxation, and market dynamics.
"""

BOOK_RECOMMENDATION_TEMPLATE = """
Based on the user's interest in {topic} and financial goals related to {goal}, 
provide recommendations from the following Indian financial books:
{book_list}

For each recommended book, explain:
1. Why it's relevant to the user's interests and goals
2. Key takeaways applicable to Indian financial context
3. How it addresses specific challenges in the Indian market
4. Practical application of the book's advice for Indian investors
"""

FINANCIAL_QA_TEMPLATE = """
Answer the following financial question for an Indian investor:
{question}

Provide:
1. A clear, concise answer tailored to the Indian financial context
2. Relevant Indian regulations, taxation considerations, or market factors
3. Common misconceptions on this topic in India (if applicable)
4. Practical next steps or additional resources
"""
