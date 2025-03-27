import requests
import logging
from datetime import datetime, timedelta
import os
from config import TAVILY_API_KEY, FINANCIAL_NEWS_SOURCES

logger = logging.getLogger(__name__)

class TavilyNewsExtractor:
    def __init__(self, api_key=None):
        self.api_key = api_key or TAVILY_API_KEY
        self.base_url = "https://api.tavily.com/search"
        
        if not self.api_key:
            logger.warning("Tavily API key not provided. News extraction functionality will be limited.")
    
    def search_indian_financial_news(self, query, max_results=10, include_domains=None, source_filter=None):
        """
        Search for Indian financial news using Tavily API
        
        Args:
            query (str): The search query
            max_results (int): Maximum number of results to return
            include_domains (list): List of domains to include in the search
            source_filter (str): Filter by specific news source
            
        Returns:
            dict: Processed news results
        """
        if not self.api_key:
            return {"error": "API key not provided", "results": []}
        
        # Add India-specific context to the query
        india_context = "Indian market" if "india" not in query.lower() else ""
        enhanced_query = f"{query} {india_context}".strip()
        
        # Default domains for Indian financial news if none specified
        if include_domains is None:
            include_domains = [
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
        
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            params = {
                "api_key": self.api_key,
                "query": enhanced_query,
                "search_depth": "advanced",
                "max_results": max_results,
                "include_domains": include_domains,
                "include_answer": True,
                "include_raw": False
            }
            
            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Process the results to extract relevant information
            processed_results = []
            if 'results' in data:
                for result in data['results']:
                    # Filter by source if specified
                    if source_filter and not any(source.lower() in result.get('source', '').lower() for source in (source_filter if isinstance(source_filter, list) else [source_filter])):
                        continue
                        
                    processed_result = {
                        'title': result.get('title', ''),
                        'url': result.get('url', ''),
                        'content': result.get('content', ''),
                        'source': result.get('source', ''),
                        'published_date': result.get('published_date', ''),
                        'score': result.get('score', 0),
                        'categories': self._categorize_news(result.get('content', ''))
                    }
                    processed_results.append(processed_result)
            
            return {
                "query": enhanced_query,
                "results": processed_results,
                "answer": data.get('answer', ''),
                "total_results": len(processed_results),
                "timestamp": datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in Tavily API request: {e}")
            return {
                "error": str(e),
                "results": [],
                "timestamp": datetime.now().isoformat()
            }
    
    def get_latest_market_news(self, market_type="NSE", limit=5):
        """
        Get the latest market news for a specific Indian market
        
        Args:
            market_type (str): Market type (NSE, BSE)
            limit (int): Maximum number of news items to return
            
        Returns:
            dict: Latest market news
        """
        query = f"latest {market_type} stock market news India"
        return self.search_indian_financial_news(query, max_results=limit)
    
    def get_policy_updates(self, limit=5):
        """
        Get the latest policy updates from RBI and SEBI
        
        Args:
            limit (int): Maximum number of updates to return
            
        Returns:
            dict: Latest policy updates
        """
        # Specifically target RBI and SEBI domains
        policy_domains = ["rbi.org.in", "sebi.gov.in"]
        query = "latest RBI SEBI policy updates regulations India"
        return self.search_indian_financial_news(
            query, 
            max_results=limit,
            include_domains=policy_domains
        )
    
    def get_company_news(self, company_name, limit=5):
        """
        Get news for a specific Indian company
        
        Args:
            company_name (str): Company name
            limit (int): Maximum number of news items
            
        Returns:
            dict: Company-specific news
        """
        query = f"{company_name} stock market news India"
        return self.search_indian_financial_news(query, max_results=limit)
    
    def get_sector_news(self, sector, limit=5):
        """
        Get news for a specific sector in India
        
        Args:
            sector (str): Sector name (e.g., IT, Banking, Pharma)
            limit (int): Maximum number of news items
            
        Returns:
            dict: Sector-specific news
        """
        query = f"India {sector} sector stock market news analysis"
        return self.search_indian_financial_news(query, max_results=limit)
    
    def search_budget_impact(self, company_or_sector=None, limit=5):
        """
        Search for impact of latest Indian budget on companies or sectors
        
        Args:
            company_or_sector (str): Company or sector name (optional)
            limit (int): Maximum number of results
            
        Returns:
            dict: Budget impact analysis
        """
        if company_or_sector:
            query = f"India budget impact on {company_or_sector}"
        else:
            query = "India latest budget impact on stock market"
        
        return self.search_indian_financial_news(query, max_results=limit)
    
    def _categorize_news(self, content):
        """
        Simple categorization of news based on content keywords
        
        Args:
            content (str): News content
            
        Returns:
            list: Categories for the news
        """
        categories = []
        content_lower = content.lower()
        
        category_keywords = {
            "Budget": ["budget", "finance minister", "fiscal", "taxation"],
            "Policy": ["policy", "rbi", "sebi", "regulation", "guideline"],
            "Markets": ["nifty", "sensex", "market", "trading", "stocks"],
            "Banking": ["bank", "banking", "loan", "interest rate", "deposit"],
            "Economy": ["gdp", "inflation", "economic growth", "recession"],
            "Corporate": ["company", "profit", "quarterly results", "earnings"],
            "Tax": ["tax", "gst", "income tax", "taxation"],
            "Investment": ["invest", "mutual fund", "portfolio", "asset"],
            "Global": ["global", "international", "foreign", "world"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                categories.append(category)
        
        return categories
