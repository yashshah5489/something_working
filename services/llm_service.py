import os
import logging
import json
from datetime import datetime
import requests
from groq import Groq
from config import GROQ_API_KEY, STOCK_ANALYSIS_TEMPLATE, NEWS_ANALYSIS_TEMPLATE, BOOK_RECOMMENDATION_TEMPLATE, FINANCIAL_QA_TEMPLATE
from services.db_service import db_service

logger = logging.getLogger(__name__)

class LLMService:
    """
    Service for interacting with Groq LLM for financial insights
    """
    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.simplified_mode = False
        
        try:
            if not self.api_key:
                logger.warning("No Groq API key provided - using simplified mode")
                self.simplified_mode = True
                self.client = None
            else:
                self.client = Groq(api_key=self.api_key)
            self.model = "llama3-70b-8192"  # Using LLaMa 3 70B model
        except Exception as e:
            logger.error(f"Error initializing Groq client: {e}")
            self.client = None
            self.simplified_mode = True
        
        # Templates
        self.stock_analysis_template = STOCK_ANALYSIS_TEMPLATE
        self.news_analysis_template = NEWS_ANALYSIS_TEMPLATE
        self.book_recommendation_template = BOOK_RECOMMENDATION_TEMPLATE
        self.financial_qa_template = FINANCIAL_QA_TEMPLATE

    def analyze_stock(self, stock_data, news_items):
        """
        Analyze a stock using the LLM based on stock data and news
        """
        try:
            # Check if in simplified mode or API key missing
            if self.simplified_mode or not self.client:
                # Provide simplified response
                symbol = stock_data.get("symbol", "Unknown")
                price = stock_data.get("current_price", "N/A")
                change = stock_data.get("day_change", "N/A")
                
                # Build simplified analysis
                return f"To analyze {symbol} stock properly, the application needs a Groq API key. " \
                       f"Current price: {price}, Daily change: {change}%. " \
                       f"For detailed analysis, please provide a valid Groq API key."
                
            # If we have API, continue with normal flow
            # Prepare news summary
            news_summary = "\n".join([
                f"- {item.get('title', 'No title')}: {item.get('summary', 'No summary')}"
                for item in news_items[:3]  # Limit to top 3 news items
            ]) if news_items else "No recent news found."
            
            # Format the prompt
            prompt = self.stock_analysis_template.format(
                stock_symbol=stock_data.get("symbol", "Unknown"),
                exchange=stock_data.get("exchange", "NSE"),
                price=stock_data.get("current_price", "N/A"),
                change=stock_data.get("day_change", "N/A"),
                volume=stock_data.get("volume", "N/A"),
                high_52week=stock_data.get("high_52week", "N/A"),
                low_52week=stock_data.get("low_52week", "N/A"),
                news_summary=news_summary
            )
            
            # Make LLM API call
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial expert specializing in Indian stock markets. Provide detailed, accurate analysis with India-specific context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1200
            )
            
            # Extract response
            analysis = completion.choices[0].message.content
            
            # Create a record of this query
            query_record = {
                "user_id": "system",  # Since this is a system-generated query
                "query_type": "stock_analysis",
                "query_text": f"Analyze {stock_data.get('symbol')} stock",
                "response": analysis,
                "sources": [news_item.get("url") for news_item in news_items if news_item.get("url")],
                "confidence_score": 0.8  # Default confidence score
            }
            db_service.save_user_query(query_record)
            
            return analysis
        
        except Exception as e:
            logger.error(f"Error analyzing stock with LLM: {e}")
            return "Unable to analyze this stock at the moment. Please try again later."

    def analyze_news(self, news_items):
        """
        Analyze a collection of news items to provide financial insights
        """
        try:
            # Check if in simplified mode or API key missing
            if self.simplified_mode or not self.client:
                # Provide simplified response
                news_count = len(news_items) if news_items else 0
                
                # Build simplified analysis
                return f"To analyze news properly, the application needs a Groq API key. " \
                       f"There are {news_count} news items available. " \
                       f"For detailed analysis, please provide a valid Groq API key."
                       
            # Format news items for the prompt
            news_texts = "\n\n".join([
                f"Title: {item.get('title', 'No title')}\n"
                f"Source: {item.get('source', 'Unknown')}\n"
                f"Date: {item.get('published_date', datetime.now()).strftime('%Y-%m-%d')}\n"
                f"Summary: {item.get('summary', 'No summary')}"
                for item in news_items[:5]  # Limit to top 5 news items
            ])
            
            # Format the prompt
            prompt = self.news_analysis_template.format(
                news_items=news_texts
            )
            
            # Make LLM API call
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial analyst specializing in Indian markets. Analyze news objectively and provide actionable insights with India-specific context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            # Extract response
            analysis = completion.choices[0].message.content
            
            # Create a record of this query
            query_record = {
                "user_id": "system",
                "query_type": "news_analysis",
                "query_text": "Analyze recent financial news",
                "response": analysis,
                "sources": [news_item.get("url") for news_item in news_items if news_item.get("url")],
                "confidence_score": 0.8
            }
            db_service.save_user_query(query_record)
            
            return analysis
        
        except Exception as e:
            logger.error(f"Error analyzing news with LLM: {e}")
            return "Unable to analyze the news at the moment. Please try again later."

    def recommend_books(self, topic, goal, book_list):
        """
        Recommend books based on user's financial topics of interest and goals
        """
        try:
            # Format the book list
            formatted_books = "\n".join([f"- {book}" for book in book_list])
            
            # Format the prompt
            prompt = self.book_recommendation_template.format(
                topic=topic,
                goal=goal,
                book_list=formatted_books
            )
            
            # Make LLM API call
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial education expert specializing in Indian personal finance. Recommend books that are particularly relevant to Indian investors and financial contexts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=1200
            )
            
            # Extract response
            recommendations = completion.choices[0].message.content
            
            # Create a record of this query
            query_record = {
                "user_id": "system",
                "query_type": "book_recommendation",
                "query_text": f"Recommend books for {topic} related to {goal}",
                "response": recommendations,
                "sources": book_list,
                "confidence_score": 0.9
            }
            db_service.save_user_query(query_record)
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error generating book recommendations with LLM: {e}")
            return "Unable to provide book recommendations at the moment. Please try again later."

    def answer_financial_question(self, question, user_id="guest"):
        """
        Answer a financial question using the LLM, enhanced with book insights
        """
        try:
            # First, get an initial LLM response
            from services.rag_service import rag_service

            # Format the initial prompt
            initial_prompt = self.financial_qa_template.format(
                question=question
            )
            
            # Make initial LLM API call
            initial_completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a financial advisor specializing in Indian personal finance, taxation, and investment. Provide accurate, detailed answers with India-specific context."},
                    {"role": "user", "content": initial_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Extract initial response
            initial_answer = initial_completion.choices[0].message.content
            
            # Get book insights to enhance the response
            enhanced_data = rag_service.enhance_llm_response(question, initial_answer)
            book_references = enhanced_data.get("book_references", [])
            insights_for_prompt = enhanced_data.get("insights_for_prompt", "")
            
            # If we have book insights, make a second call to weave them into the response
            if insights_for_prompt:
                # Create a new prompt with book insights included
                enhanced_prompt = f"{initial_prompt}\n{insights_for_prompt}\n\nPlease incorporate these book insights into your answer, weaving them naturally and seamlessly into your explanation. Don't simply list them as quotes or references."
                
                # Make enhanced LLM API call
                enhanced_completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a financial advisor specializing in Indian personal finance, taxation, and investment. Provide accurate, detailed answers with India-specific context. When insights from financial books are provided, weave them naturally into your response."},
                        {"role": "user", "content": enhanced_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1200
                )
                
                # Extract enhanced response
                enhanced_answer = enhanced_completion.choices[0].message.content
                final_answer = enhanced_answer
            else:
                # No book insights available, use initial response
                final_answer = initial_answer
                
            # Prepare sources list from book references for database storage
            sources = []
            for ref in book_references:
                sources.append({
                    "title": ref.get("title"),
                    "author": ref.get("author"),
                    "content_snippet": ref.get("content")[:100] + "..." if len(ref.get("content", "")) > 100 else ref.get("content", "")
                })
            
            # Create a record of this query
            query_record = {
                "user_id": user_id,
                "query_type": "financial_qa",
                "query_text": question,
                "response": final_answer,
                "sources": sources,
                "confidence_score": 0.85 if book_references else 0.8
            }
            db_service.save_user_query(query_record)
            
            # Return both the answer and book references for frontend display
            return {
                "answer": final_answer,
                "book_references": book_references
            }
        
        except Exception as e:
            logger.error(f"Error answering financial question with LLM: {e}")
            return "I'm unable to answer your question at the moment. Please try again later."

# Create instance of the service
llm_service = LLMService()
