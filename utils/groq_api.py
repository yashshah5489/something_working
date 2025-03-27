import os
import logging
import requests
import json
from datetime import datetime
from config import GROQ_API_KEY

logger = logging.getLogger(__name__)

class GroqLLMProcessor:
    def __init__(self, api_key=None):
        self.api_key = api_key or GROQ_API_KEY
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama3-70b-8192"  # Default model
        
        if not self.api_key:
            logger.warning("Groq API key not provided. LLM functionality will be limited.")
    
    def get_financial_insights(self, context, query, model=None):
        """
        Get financial insights from Groq LLM
        
        Args:
            context (str/dict): Context information (news, stock data, etc.)
            query (str): User query for financial insights
            model (str): Groq LLM model to use
            
        Returns:
            dict: LLM response with financial insights
        """
        if not self.api_key:
            return {"error": "API key not provided", "insights": ""}
        
        try:
            model = model or self.model
            
            # Convert context to string if it's not already
            if isinstance(context, dict):
                context_str = json.dumps(context, indent=2)
            else:
                context_str = str(context)
            
            # Create India-specific financial analysis prompt
            messages = [
                {
                    "role": "system",
                    "content": """You are an expert financial analyst specializing in Indian markets. 
                    Your analysis is based on Indian economic policies, RBI regulations, SEBI guidelines, 
                    taxation frameworks, and market trends. Provide insights that are specific to Indian 
                    investors and market conditions. Your advice should consider:
                    
                    1. India-specific tax implications (STCG, LTCG, STT, etc.)
                    2. Indian regulatory environment and compliance requirements
                    3. RBI and SEBI policies that impact investments
                    4. Indian market dynamics and sector-specific trends
                    5. Local investment options (PPF, NPS, ELSS, etc.)
                    
                    Always clarify when international concepts may not apply directly to India."""
                },
                {
                    "role": "user",
                    "content": f"Given the following information about Indian markets:\n\n{context_str}\n\n{query}"
                }
            ]
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.1,  # Lower temperature for more focused answers
                "max_tokens": 2048
            }
            
            response = requests.post(
                self.base_url, 
                headers=headers, 
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            insights = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            return {
                "query": query,
                "insights": insights,
                "model": model,
                "timestamp": datetime.now().isoformat()
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in Groq API request: {e}")
            return {
                "error": str(e),
                "insights": "",
                "timestamp": datetime.now().isoformat()
            }
    
    def analyze_stock(self, stock_data, stock_symbol, additional_context=None):
        """
        Analyze stock data and provide insights
        
        Args:
            stock_data (dict): Stock data including price history, financials, etc.
            stock_symbol (str): Stock symbol (e.g., RELIANCE.NS)
            additional_context (str): Any additional context for analysis
            
        Returns:
            dict: Analysis and recommendations
        """
        # Create context with stock data
        context = f"Stock Symbol: {stock_symbol}\n\nStock Data: {json.dumps(stock_data, indent=2)}"
        
        if additional_context:
            context += f"\n\nAdditional Context: {additional_context}"
        
        query = f"""
        Please analyze this Indian stock ({stock_symbol}) and provide:
        1. A summary of current performance
        2. Key financial indicators and what they suggest
        3. Potential strengths and weaknesses
        4. Short-term and long-term outlook
        5. Any specific considerations for Indian investors (tax implications, regulatory factors)
        """
        
        return self.get_financial_insights(context, query)
    
    def interpret_news_impact(self, news_data, stock_symbols=None):
        """
        Interpret the potential impact of news on stocks or the market
        
        Args:
            news_data (dict): News data to interpret
            stock_symbols (list): List of stock symbols to analyze impact on
            
        Returns:
            dict: Analysis of news impact
        """
        # Create context with news data
        if isinstance(news_data, dict) and 'results' in news_data:
            news_items = "\n\n".join([
                f"Title: {item.get('title', '')}\nSource: {item.get('source', '')}\nContent: {item.get('content', '')}"
                for item in news_data.get('results', [])
            ])
        else:
            news_items = str(news_data)
        
        context = f"News Data:\n{news_items}"
        
        # Add stock context if provided
        if stock_symbols:
            stocks_str = ", ".join(stock_symbols)
            query = f"""
            Based on these news items about Indian markets, analyze:
            1. Potential impact on these specific stocks: {stocks_str}
            2. Market sentiment implications
            3. How Indian investors should interpret this news
            4. Any policy or regulatory implications
            5. Recommended actions for investors based on this news
            """
        else:
            query = """
            Based on these news items about Indian markets, analyze:
            1. Potential impact on the Indian market overall
            2. Sectors likely to be affected and how
            3. How Indian investors should interpret this news
            4. Any policy or regulatory implications
            5. Recommended investment strategies based on this news
            """
        
        return self.get_financial_insights(context, query)
    
    def explain_financial_concept(self, concept):
        """
        Explain a financial concept in the Indian context
        
        Args:
            concept (str): Financial concept to explain
            
        Returns:
            dict: Explanation of the concept
        """
        query = f"""
        Please explain the concept of '{concept}' specifically in the Indian financial context.
        Include:
        1. What it means in India
        2. How it works in Indian markets/regulations
        3. Relevant Indian laws, regulations, or policies
        4. How it might differ from international standards
        5. Practical implications for Indian investors
        """
        
        return self.get_financial_insights({}, query)
    
    def get_tax_advice(self, investment_type, holding_period=None, income_bracket=None):
        """
        Get tax advice for specific investment types in India
        
        Args:
            investment_type (str): Type of investment (stocks, mutual funds, etc.)
            holding_period (str): Holding period if applicable
            income_bracket (str): Income tax bracket if applicable
            
        Returns:
            dict: Tax advice for the investment
        """
        context = {
            "investment_type": investment_type,
            "holding_period": holding_period,
            "income_bracket": income_bracket
        }
        
        query = f"""
        Provide detailed tax advice for {investment_type} investments in India.
        
        {f"Holding Period: {holding_period}" if holding_period else ""}
        {f"Income Tax Bracket: {income_bracket}" if income_bracket else ""}
        
        Include:
        1. Applicable tax rates (STCG, LTCG as relevant)
        2. Tax-saving strategies within legal framework
        3. Important deadlines or filing requirements
        4. Recent changes in taxation rules (if any)
        5. Tax implications of different exit strategies
        """
        
        return self.get_financial_insights(context, query)
    
    def compare_investments(self, investments, criteria=None):
        """
        Compare different investment options in the Indian context
        
        Args:
            investments (list): List of investment types to compare
            criteria (list): Criteria for comparison
            
        Returns:
            dict: Comparative analysis
        """
        investments_str = ", ".join(investments)
        
        if criteria:
            criteria_str = ", ".join(criteria)
            context = f"Investments to compare: {investments_str}\nComparison criteria: {criteria_str}"
        else:
            context = f"Investments to compare: {investments_str}"
            criteria_str = "risk, returns, liquidity, tax implications, and suitability"
        
        query = f"""
        Compare these investment options in the Indian financial context: {investments_str}
        
        Analyze them based on {criteria_str}.
        
        For each option, provide:
        1. Typical returns in the Indian market
        2. Risk assessment specific to Indian conditions
        3. Tax treatment under Indian tax laws
        4. Liquidity considerations
        5. Suitable investor profiles in India
        6. Any special regulatory considerations in India
        """
        
        return self.get_financial_insights(context, query)
