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

# India-specific constants
INDIAN_STOCK_EXCHANGES = ["NSE", "BSE"]
DEFAULT_STOCK_EXCHANGE = "NSE"

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

# Popular Indian financial books for RAG
FINANCIAL_BOOKS = [
    "Let's Talk Money by Monika Halan",
    "The Intelligent Investor by Benjamin Graham",
    "Rich Dad Poor Dad by Robert Kiyosaki",
    "Bulls, Bears and Other Beasts by Santosh Nair",
    "I Do What I Do by Raghuram Rajan",
    "Financial Intelligence by Karen Berman",
    "The 5 Mistakes Every Investor Makes by Peter Mallouk",
    "Stocks to Riches by Parag Parikh"
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
