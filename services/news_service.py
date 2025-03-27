import os
import logging
import json
import requests
from datetime import datetime, timedelta
from services.db_service import db_service
from config import TAVILY_API_KEY, INDIAN_NEWS_SOURCES

logger = logging.getLogger(__name__)

class NewsService:
    """
    Service for retrieving and processing financial news from India
    using Tavily API
    """
    def __init__(self):
        self.api_key = TAVILY_API_KEY
        self.api_endpoint = "https://api.tavily.com/search"
        self.indian_news_sources = INDIAN_NEWS_SOURCES

    def get_financial_news(self, query="Indian financial news", max_results=10):
        """
        Retrieve financial news related to the Indian market using Tavily API
        """
        try:
            params = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": "advanced",
                "include_domains": [
                    "economictimes.indiatimes.com",
                    "business-standard.com",
                    "livemint.com", 
                    "financialexpress.com",
                    "moneycontrol.com",
                    "ndtv.com",
                    "bloombergquint.com",
                    "rbi.org.in",
                    "sebi.gov.in"
                ],
                "include_answer": True,
                "include_images": False,
                "max_results": max_results,
                "include_raw_content": True
            }
            
            response = requests.post(self.api_endpoint, json=params)
            response.raise_for_status()
            
            result = response.json()
            
            # Process the results and format them
            processed_news = []
            if "results" in result:
                for item in result["results"]:
                    # Extract source from URL or use domain name
                    source = item.get("source", "Unknown")
                    for known_source in self.indian_news_sources:
                        if known_source.lower() in source.lower():
                            source = known_source
                            break
                    
                    # Parse published date (or use current time if unavailable)
                    try:
                        published_date = datetime.fromisoformat(item.get("published_date", datetime.now().isoformat()))
                    except:
                        published_date = datetime.now()
                    
                    # Create news item
                    news_item = {
                        "title": item.get("title", ""),
                        "source": source,
                        "url": item.get("url", ""),
                        "published_date": published_date,
                        "content": item.get("raw_content", ""),
                        "summary": item.get("content", ""),
                        "relevance_score": float(item.get("score", 0)),
                        "related_stocks": self._extract_stock_mentions(item.get("raw_content", "")),
                        "sentiment": "neutral"  # Default sentiment
                    }
                    
                    # Save to database
                    db_service.save_news_item(news_item)
                    processed_news.append(news_item)
            
            return processed_news
        
        except Exception as e:
            logger.error(f"Error fetching news from Tavily: {e}")
            return []

    def get_stock_specific_news(self, stock_symbol, exchange="NSE", max_results=5):
        """
        Get news specifically about a given stock
        """
        try:
            # Create a query specific to the stock
            query = f"{stock_symbol} {exchange} stock news India"
            news = self.get_financial_news(query=query, max_results=max_results)
            
            # Filter for relevance
            relevant_news = [
                item for item in news 
                if stock_symbol in item.get("title", "") or 
                   stock_symbol in item.get("content", "") or
                   stock_symbol in item.get("related_stocks", [])
            ]
            
            return relevant_news
        
        except Exception as e:
            logger.error(f"Error fetching stock specific news: {e}")
            return []

    def get_rbi_sebi_updates(self, max_results=5):
        """
        Get latest updates from RBI and SEBI
        """
        try:
            query = "latest RBI SEBI regulations India financial market"
            return self.get_financial_news(query=query, max_results=max_results)
        
        except Exception as e:
            logger.error(f"Error fetching RBI/SEBI updates: {e}")
            return []

    def get_budget_economic_news(self, max_results=5):
        """
        Get news related to Indian budget and economic policies
        """
        try:
            query = "India budget economic policy financial market impact"
            return self.get_financial_news(query=query, max_results=max_results)
        
        except Exception as e:
            logger.error(f"Error fetching budget/economic news: {e}")
            return []

    def _extract_stock_mentions(self, text):
        """
        Extract potential stock symbols mentioned in the text
        This is a simple implementation - in a production system, 
        you would want to use NER or a more sophisticated approach
        """
        # Common Indian stock symbols (a small sample)
        common_symbols = [
            "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", 
            "SBIN", "BAJFINANCE", "ICICIBANK", "ITC", "KOTAKBANK",
            "AXISBANK", "LT", "MARUTI", "ASIANPAINT", "TITAN",
            "WIPRO", "ONGC", "TECHM", "BAJAJFINSV", "HCLTECH"
        ]
        
        mentioned_stocks = []
        if text:
            for symbol in common_symbols:
                if symbol in text.upper():
                    mentioned_stocks.append(symbol)
        
        return mentioned_stocks

# Create instance of the service
news_service = NewsService()
