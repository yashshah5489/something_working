import os
import logging
import json
from datetime import datetime
from langchain.vectorstores import FAISS
# Commented out until sentence-transformers package is installed
# from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from config import FINANCIAL_BOOKS
from services.db_service import db_service

logger = logging.getLogger(__name__)

class RAGService:
    """
    Service for Retrieval-Augmented Generation (RAG) using book insights
    """
    def __init__(self):
        try:
            # Simplified initialization without HuggingFaceEmbeddings
            # This is a temporary measure until dependencies are resolved
            logger.warning("Initializing RAG Service in simplified mode")
            
            # Book data - In production, this would come from a database or files
            self.books_data = self._initialize_book_data()
            
            # Skip vector store initialization
            self.vector_store = None
            self.embeddings = None
            self.text_splitter = None
            
            logger.info("RAG Service initialized in simplified mode")
        except Exception as e:
            logger.error(f"Error initializing RAG Service: {e}")
            self.vector_store = None

    def _initialize_book_data(self):
        """
        Initialize book data - in a real implementation, this would
        be loaded from files or a database. For now, we'll use a simplified version.
        """
        books_data = {}
        
        try:
            # Check if we have book data in the database
            db_books = db_service.get_book_insights()
            
            if db_books and len(db_books) > 0:
                for book in db_books:
                    # Handle both dictionary and SQLAlchemy model objects
                    if hasattr(book, 'book_title'):
                        # It's a SQLAlchemy model
                        book_title = book.book_title
                        books_data[book_title] = {
                            "author": book.author,
                            "content": book.summary if book.summary else "",
                            "insights": book.insights if book.insights else [],
                            "topics": book.topics if book.topics else []
                        }
                    elif isinstance(book, dict) and "book_title" in book:
                        # It's a dictionary
                        book_title = book["book_title"]
                        books_data[book_title] = {
                            "author": book.get("author", "Unknown"),
                            "content": book.get("summary", ""),
                            "insights": book.get("insights", []),
                            "topics": book.get("topics", [])
                        }
            
            # If no books were loaded, use default data
            if not books_data:
                logger.warning("No books found in database, using default book data")
                # Default book data
                books_data = {
                    "Let's Talk Money by Monika Halan": {
                        "author": "Monika Halan",
                        "content": """Let's Talk Money is a comprehensive guide to managing personal finances in India. 
                        The book covers essential topics like budgeting, insurance, investments, retirement planning, and tax planning 
                        with specific focus on Indian financial products and regulations. 
                        Key insights include the Serenity System for organizing finances, the importance of term insurance 
                        over traditional policies, and investment strategies for Indians across different age groups and risk profiles.""",
                        "insights": [
                            "The Serenity System: A three-jar approach to organizing your money",
                            "Term insurance is the most cost-effective life insurance in India",
                            "Diversify investments across equity, debt, and gold based on your time horizon",
                            "Understand the tax implications of different investment options in India"
                        ],
                        "topics": ["Personal Finance", "Budgeting", "Insurance", "Investments", "Tax Planning"]
                    },
                    "The Intelligent Investor by Benjamin Graham": {
                        "author": "Benjamin Graham",
                        "content": """The Intelligent Investor is a classic investment guide that promotes value investing principles.
                        While written with US markets in mind, the core principles apply to Indian investors as well.
                        The book emphasizes fundamental analysis, margin of safety, and long-term investment strategies.
                        Indian investors can apply these concepts to BSE and NSE listed companies by focusing on
                        strong fundamentals, reasonable valuations, and avoiding market speculation.""",
                        "insights": [
                            "Value investing focuses on intrinsic value rather than market trends",
                            "Mr. Market analogy explains market volatility and irrational behavior",
                            "Margin of safety is essential for risk management in Indian equity markets",
                            "Defensive vs. Enterprising investor strategies can be applied to Indian portfolios"
                        ],
                        "topics": ["Value Investing", "Stock Analysis", "Risk Management", "Market Psychology"]
                    },
                    "Rich Dad Poor Dad by Robert Kiyosaki": {
                        "author": "Robert Kiyosaki",
                        "content": """Rich Dad Poor Dad contrasts the financial philosophies of the author's two father figures.
                        For Indian readers, the book's emphasis on financial education and asset building is particularly relevant.
                        The concepts of assets vs. liabilities can be applied to Indian investments like real estate, stocks, and business ownership.
                        The book's tax strategies, however, need to be adapted to Indian taxation laws and regulations.""",
                        "insights": [
                            "Build assets that generate passive income rather than working for money",
                            "Financial literacy is critical and often missing from traditional education in India",
                            "Understanding the difference between assets and liabilities in the Indian context",
                            "Entrepreneurship as a path to wealth creation for Indian professionals"
                        ],
                        "topics": ["Financial Education", "Asset Building", "Passive Income", "Entrepreneurship"]
                    }
                }
                
                # Save these to the database
                try:
                    for title, data in books_data.items():
                        book_insight = {
                            "book_title": title,
                            "author": data["author"],
                            "topics": data["topics"],
                            "insights": data["insights"],
                            "relevance_categories": data["topics"][:2],  # Just use the first two topics as categories
                            "summary": data["content"]
                        }
                        db_service.save_book_insight(book_insight)
                except Exception as e:
                    logger.error(f"Could not save default books to database: {e}")
        
        except Exception as e:
            logger.error(f"Error initializing book data: {e}")
            # Fallback to default books data structure without DB interaction
            books_data = {
                "Let's Talk Money by Monika Halan": {
                    "author": "Monika Halan",
                    "content": "Guide to managing personal finances in India.",
                    "insights": ["Term insurance is important", "Diversify investments"],
                    "topics": ["Personal Finance", "Investments"]
                },
                "The Intelligent Investor": {
                    "author": "Benjamin Graham",
                    "content": "Classic investment guide that promotes value investing principles.",
                    "insights": ["Value investing focuses on intrinsic value"],
                    "topics": ["Value Investing", "Stock Analysis"]
                }
            }
            
        return books_data

    def _create_vector_store(self):
        """
        Create a vector store from book data
        """
        try:
            documents = []
            
            for book_title, book_data in self.books_data.items():
                # Create documents from book content
                doc = Document(
                    page_content=book_data["content"],
                    metadata={
                        "source": book_title,
                        "author": book_data["author"],
                        "topics": book_data["topics"]
                    }
                )
                documents.append(doc)
                
                # Create documents from each insight
                for insight in book_data["insights"]:
                    doc = Document(
                        page_content=insight,
                        metadata={
                            "source": book_title,
                            "author": book_data["author"],
                            "type": "insight"
                        }
                    )
                    documents.append(doc)
            
            # Split documents into chunks
            chunks = self.text_splitter.split_documents(documents)
            
            # Create vector store
            vector_store = FAISS.from_documents(chunks, self.embeddings)
            
            return vector_store
        
        except Exception as e:
            logger.error(f"Error creating vector store: {e}")
            return None

    def retrieve_relevant_content(self, query, k=5):
        """
        Retrieve relevant content from books based on a query
        In simplified mode, uses basic keyword matching instead of vector search
        """
        try:
            if not self.vector_store:
                logger.warning("Using simplified keyword search instead of vector search")
                # Simple fallback using keyword matching
                results = []
                query_lower = query.lower()
                
                # For each book, check if query terms appear in content
                for book_title, book_data in self.books_data.items():
                    content = book_data.get("content", "")
                    if any(term.lower() in content.lower() for term in query.split() if len(term) > 3):
                        results.append({
                            "content": content[:200] + "...",  # First 200 chars
                            "source": book_title,
                            "author": book_data.get("author", "Unknown"),
                            "type": "content"
                        })
                    
                    # Also check insights
                    for insight in book_data.get("insights", []):
                        if any(term.lower() in insight.lower() for term in query.split() if len(term) > 3):
                            results.append({
                                "content": insight,
                                "source": book_title,
                                "author": book_data.get("author", "Unknown"),
                                "type": "insight"
                            })
                
                # Return top k results
                return results[:k]
            
            # This code will not be reached in simplified mode
            # Search for relevant documents
            docs = self.vector_store.similarity_search(query, k=k)
            
            results = []
            for doc in docs:
                results.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "Unknown"),
                    "author": doc.metadata.get("author", "Unknown"),
                    "type": doc.metadata.get("type", "content")
                })
            
            return results
        
        except Exception as e:
            logger.error(f"Error retrieving content: {e}")
            return []

    def get_book_recommendations(self, query, top_n=3):
        """
        Get book recommendations based on a query
        """
        try:
            # Get relevant content first
            relevant_content = self.retrieve_relevant_content(query)
            
            # Extract unique book sources
            recommended_books = {}
            
            for item in relevant_content:
                source = item.get("source")
                if source and source not in recommended_books:
                    book_data = self.books_data.get(source, {})
                    recommended_books[source] = {
                        "title": source,
                        "author": book_data.get("author", "Unknown"),
                        "topics": book_data.get("topics", []),
                        "relevance": self._calculate_relevance(query, book_data),
                        "key_insights": book_data.get("insights", [])[:3]  # Top 3 insights
                    }
            
            # Sort by relevance and get top N
            sorted_recommendations = sorted(
                recommended_books.values(),
                key=lambda x: x["relevance"],
                reverse=True
            )[:top_n]
            
            return sorted_recommendations
        
        except Exception as e:
            logger.error(f"Error getting book recommendations: {e}")
            return []

    def _calculate_relevance(self, query, book_data):
        """
        Calculate relevance score of a book to a query
        Simple implementation - in production, you'd use better similarity metrics
        """
        relevance = 0
        
        # Add relevance based on topics
        query_lower = query.lower()
        for topic in book_data.get("topics", []):
            if topic.lower() in query_lower:
                relevance += 0.3
        
        # Add relevance based on content
        content = book_data.get("content", "")
        words = query.split()
        for word in words:
            if len(word) > 3 and word.lower() in content.lower():
                relevance += 0.1
        
        # Ensure relevance is between 0 and 1
        return min(relevance, 1.0)

    def enhance_llm_response(self, query, llm_response):
        """
        Enhance LLM response with relevant book content
        Returns both enhanced response and book references separately
        """
        try:
            relevant_content = self.retrieve_relevant_content(query, k=3)
            
            if not relevant_content:
                return {
                    "response": llm_response,
                    "book_references": []
                }
            
            # Create a list of book references for separate display
            book_references = []
            for item in relevant_content:
                book_references.append({
                    "title": item['source'],
                    "author": item['author'],
                    "content": item['content'],
                    "type": item.get('type', 'content')
                })
            
            # Format content to be added to the LLM prompt for reprocessing
            # This will allow the LLM to weave the book insights into its response
            book_insights_for_prompt = "\n\nRelevant insights from financial books that may help with this question:\n"
            
            for i, item in enumerate(relevant_content, 1):
                book_insights_for_prompt += f"- {item['content']} (From: {item['source']})\n"
            
            # The caller should use these book insights to enhance the prompt and get a new response
            # Return both the original response and book references
            return {
                "response": llm_response,
                "book_references": book_references,
                "insights_for_prompt": book_insights_for_prompt
            }
        
        except Exception as e:
            logger.error(f"Error enhancing LLM response: {e}")
            return {
                "response": llm_response,
                "book_references": []
            }

# Create a placeholder for the service instance
rag_service = None

def init_rag_service():
    """Initialize the RAG service within application context"""
    global rag_service
    rag_service = RAGService()
    return rag_service
