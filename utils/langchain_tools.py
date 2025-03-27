import os
import logging
from langchain.llms import Groq
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.embeddings import HuggingFaceEmbeddings
from config import GROQ_API_KEY

logger = logging.getLogger(__name__)

class LangChainManager:
    def __init__(self, api_key=None):
        self.api_key = api_key or GROQ_API_KEY
        
        if not self.api_key:
            logger.warning("Groq API key not provided. LangChain functionality will be limited.")
            self.llm = None
        else:
            # Initialize Groq LLM
            self.llm = Groq(
                api_key=self.api_key,
                model_name="llama3-70b-8192"  # Default model
            )
        
        # Initialize embeddings model for RAG
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-mpnet-base-v2"
            )
        except Exception as e:
            logger.error(f"Error initializing embeddings model: {e}")
            self.embeddings = None
    
    def create_qa_chain(self, docs, prompt_template=None):
        """
        Create a question-answering chain with the given documents
        
        Args:
            docs (list): List of documents or text for context
            prompt_template (str): Custom prompt template
            
        Returns:
            RetrievalQA: QA chain for financial questions
        """
        if not self.llm or not self.embeddings:
            logger.error("LLM or embeddings not initialized properly")
            return None
        
        try:
            # Convert to Document objects if they're just strings
            documents = []
            for doc in docs:
                if isinstance(doc, str):
                    documents.append(Document(page_content=doc))
                elif isinstance(doc, dict) and 'content' in doc:
                    documents.append(Document(page_content=doc['content'], metadata=doc.get('metadata', {})))
                else:
                    documents.append(doc)
            
            # Split text
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, 
                chunk_overlap=200
            )
            splits = text_splitter.split_documents(documents)
            
            # Create vector store
            vectorstore = FAISS.from_documents(splits, self.embeddings)
            retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
            
            # Create default financial QA prompt if none provided
            if not prompt_template:
                prompt_template = """
                You are a financial advisor with expertise in Indian financial markets, regulations, and investment strategies.
                Use the following pieces of context to answer the question at the end.
                If you don't know the answer, just say that you don't know, don't try to make up an answer.
                Always consider Indian financial context, regulations, and market conditions.
                
                Context: {context}
                
                Question: {question}
                
                Helpful Answer:
                """
            
            PROMPT = PromptTemplate(
                template=prompt_template, 
                input_variables=["context", "question"]
            )
            
            # Create chain
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": PROMPT}
            )
            
            return qa_chain
        
        except Exception as e:
            logger.error(f"Error creating QA chain: {e}")
            return None
    
    def get_financial_advice(self, qa_chain, question):
        """
        Get financial advice using the QA chain
        
        Args:
            qa_chain: RetrievalQA chain
            question (str): Financial question
            
        Returns:
            dict: Answer and source documents
        """
        if not qa_chain:
            return {
                "answer": "Sorry, the QA system is not available at the moment.",
                "sources": []
            }
        
        try:
            # Add India-specific context if not already present
            if "india" not in question.lower() and "indian" not in question.lower():
                question = f"In the Indian financial context: {question}"
            
            result = qa_chain({"query": question})
            
            # Extract sources
            sources = []
            if result.get("source_documents"):
                for doc in result["source_documents"]:
                    if hasattr(doc, "metadata") and doc.metadata:
                        sources.append({
                            "content": doc.page_content[:200] + "...",
                            "metadata": doc.metadata
                        })
                    else:
                        sources.append({
                            "content": doc.page_content[:200] + "..."
                        })
            
            return {
                "question": question,
                "answer": result.get("result", "No answer found."),
                "sources": sources
            }
        
        except Exception as e:
            logger.error(f"Error getting financial advice: {e}")
            return {
                "question": question,
                "answer": f"An error occurred: {str(e)}",
                "sources": []
            }
    
    def create_investment_advisor(self, market_data, news_data, book_insights):
        """
        Create a specialized investment advisor with multiple knowledge sources
        
        Args:
            market_data (dict): Current market data
            news_data (dict): Recent financial news
            book_insights (dict): Insights from financial books
            
        Returns:
            object: Investment advisor chain
        """
        # Prepare documents from multiple sources
        docs = []
        
        # Add market data
        if market_data:
            market_str = f"Current Market Data: {str(market_data)}"
            docs.append(Document(
                page_content=market_str,
                metadata={"source": "market_data", "date": market_data.get("timestamp", "")}
            ))
        
        # Add news data
        if news_data and "results" in news_data:
            for item in news_data.get("results", []):
                docs.append(Document(
                    page_content=f"Title: {item.get('title', '')}\nSource: {item.get('source', '')}\nContent: {item.get('content', '')}",
                    metadata={"source": "news", "title": item.get("title", ""), "date": item.get("published_date", "")}
                ))
        
        # Add book insights
        if book_insights:
            for book, insights in book_insights.items():
                docs.append(Document(
                    page_content=f"Book: {book}\nInsights: {insights}",
                    metadata={"source": "book", "title": book}
                ))
        
        # Create specialized prompt for investment advice
        prompt_template = """
        You are an expert investment advisor specializing in Indian financial markets.
        You have deep knowledge of Indian tax laws, investment regulations, and market dynamics.
        
        Use the following context information to provide personalized investment advice.
        The context includes current market data, recent news, and insights from respected financial books.
        
        Always frame your advice in the Indian context, considering:
        - Indian tax implications (including STCG, LTCG, STT, etc.)
        - RBI and SEBI regulations
        - India-specific investment vehicles (like PPF, NPS, ELSS, etc.)
        - Current market conditions in Indian exchanges (NSE/BSE)
        
        Context: {context}
        
        Question: {question}
        
        Comprehensive Investment Advice:
        """
        
        # Create and return the specialized QA chain
        return self.create_qa_chain(docs, prompt_template)
    
    def create_tax_advisor(self, tax_regulations):
        """
        Create a specialized tax advisor for Indian investors
        
        Args:
            tax_regulations (list): List of tax regulations and information
            
        Returns:
            object: Tax advisor chain
        """
        # Prepare tax documents
        docs = []
        for reg in tax_regulations:
            if isinstance(reg, str):
                docs.append(Document(page_content=reg, metadata={"source": "tax_regulation"}))
            elif isinstance(reg, dict):
                docs.append(Document(
                    page_content=reg.get("content", ""),
                    metadata={"source": "tax_regulation", "title": reg.get("title", "")}
                ))
        
        # Create specialized prompt for tax advice
        prompt_template = """
        You are an expert tax advisor specializing in Indian tax laws and regulations for investors.
        Your advice is accurate, up-to-date, and tailored to the Indian tax framework.
        
        Use the following tax regulations and information to answer the question.
        Be specific about tax rates, exemptions, deductions, and filing requirements in India.
        
        When relevant, mention:
        - Different tax treatment for different asset classes in India
        - Holding period classifications (short-term vs long-term)
        - Applicable surcharges and cesses
        - Tax-saving investment options under various sections
        - Recent changes to tax laws that might impact the answer
        
        Context: {context}
        
        Question: {question}
        
        Detailed Tax Advice:
        """
        
        # Create and return the specialized QA chain
        return self.create_qa_chain(docs, prompt_template)
