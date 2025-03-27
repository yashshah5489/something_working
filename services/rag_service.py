import os
import logging
import json
from datetime import datetime
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from config import FINANCIAL_BOOKS
from services.db_service import db_service

logger = logging.getLogger(__name__)

class RAGService:
    """
    Service for Retrieval-Augmented Generation (RAG) using book insights
    """
    def __init__(self):
        try:
            # Initialize embeddings model
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            
            # Initialize text splitter for chunking
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            
            # Book data - In production, this would come from a database or files
            self.books_data = self._initialize_book_data()
            
            # Create vector store
            self.vector_store = self._create_vector_store()
            
            logger.info("RAG Service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing RAG Service: {e}")
            self.vector_store = None

    def _initialize_book_data(self):
        """
        Initialize book data - in a real implementation, this would
        be loaded from files or a database. For now, we'll use a simplified version.
        """
        books_data = {}
        
        # Check if we have book data in the database
        db_books = db_service.get_book_insights()
        
        if db_books:
            for book in db_books:
                book_title = book.get("book_title")
                if book_title:
                    books_data[book_title] = {
                        "author": book.get("author", "Unknown"),
                        "content": book.get("summary", ""),
                        "insights": book.get("insights", []),
                        "topics": book.get("topics", [])
                    }
        else:
            # If no books in database, use simplified mock data
            # In production, you would extract this from actual book content
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
        """
        try:
            if not self.vector_store:
                logger.error("Vector store not initialized")
                return []
            
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
            logger.error(f"Error retrieving content from vector store: {e}")
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
        """
        try:
            relevant_content = self.retrieve_relevant_content(query, k=3)
            
            if not relevant_content:
                return llm_response
            
            # Format relevant content as citations
            citations = "\n\n**Supporting Information from Financial Books:**\n"
            
            for i, item in enumerate(relevant_content, 1):
                citations += f"{i}. \"{item['content']}\" - {item['source']} by {item['author']}\n\n"
            
            # Combine with original response
            enhanced_response = f"{llm_response}\n{citations}"
            
            return enhanced_response
        
        except Exception as e:
            logger.error(f"Error enhancing LLM response: {e}")
            return llm_response

# Create instance of the service
rag_service = RAGService()
