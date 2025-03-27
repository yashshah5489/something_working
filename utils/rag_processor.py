import os
import logging
import json
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.llms import Groq
from config import GROQ_API_KEY, FINANCIAL_BOOKS, RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP

logger = logging.getLogger(__name__)

class RAGProcessor:
    def __init__(self, api_key=None):
        self.api_key = api_key or GROQ_API_KEY
        self.financial_books = FINANCIAL_BOOKS
        self.book_content = {}
        
        # Initialize embeddings
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-mpnet-base-v2"
            )
        except Exception as e:
            logger.error(f"Error initializing embeddings model: {e}")
            self.embeddings = None
        
        # Initialize LLM if API key is available
        if self.api_key:
            self.llm = Groq(
                api_key=self.api_key,
                model_name="llama3-70b-8192"
            )
        else:
            logger.warning("Groq API key not provided. RAG functionality will be limited.")
            self.llm = None
        
        # Load predefined book content for India-specific financial books
        self._load_book_content()
    
    def _load_book_content(self):
        """
        Load predefined content for financial books
        In a real application, this would load actual book content from files
        For this implementation, we'll use summaries and key insights
        """
        # Let's Talk Money by Monika Halan
        self.book_content["Let's Talk Money"] = """
        Let's Talk Money by Monika Halan is a personal finance guide tailored for Indians.
        
        Key insights:
        1. Financial Planning: Create a robust financial plan with three bank accounts - income, spending, and investments.
        
        2. Emergency Fund: Maintain an emergency fund equivalent to 6-12 months of expenses in a liquid fund.
        
        3. Insurance: Buy term insurance worth 10 times your annual income. Get adequate health insurance separate from employer coverage.
        
        4. Investments: Follow a systematic investment approach with a mix of EPF/PPF, equity mutual funds, and NPS.
        
        5. Tax Planning: Use Section 80C investments strategically, including ELSS mutual funds for tax-saving with equity exposure.
        
        6. Real Estate: Avoid treating real estate as the only investment avenue. Consider financial assets for better liquidity.
        
        7. Gold: Invest in gold bonds or ETFs rather than physical gold for better returns and safety.
        
        8. Debt Management: Avoid high-interest consumer loans and credit card debt. Prioritize mortgage payoff.
        
        India-specific strategies:
        - Use PPF for tax-efficient debt allocation
        - Maximize EPF contributions through VPF
        - Utilize Sukanya Samriddhi Yojana for girl child education
        - Consider NPS for additional tax benefits under 80CCD(1B)
        - Use ELSS funds for tax-saving with shortest lock-in period
        
        The book emphasizes simplicity, discipline, and long-term thinking over market timing and complex products.
        """
        
        # The Intelligent Investor
        self.book_content["The Intelligent Investor"] = """
        The Intelligent Investor by Benjamin Graham is a classic guide on value investing with principles applicable to Indian markets.
        
        Key insights for Indian investors:
        
        1. Margin of Safety: Always invest with a margin of safety - the difference between intrinsic value and market price. In volatile Indian markets, this principle is especially important.
        
        2. Mr. Market Metaphor: The market behaves like a manic-depressive person, offering both overvalued and undervalued prices. Indian markets often show emotional extremes.
        
        3. Defensive vs. Enterprising Investor: Defensive investors should focus on large-cap blue-chip stocks in India (like HDFC Bank, TCS, Reliance). Enterprising investors can explore undervalued mid and small-caps.
        
        4. Fundamental Analysis: Focus on companies with strong fundamentals, consistent dividend history, and low debt. In India, sectors like FMCG and IT services often provide stable fundamentals.
        
        5. Price-to-Earnings Ratio: Look for companies with reasonable P/E ratios relative to growth. Indian markets sometimes have higher average P/Es than Western markets.
        
        6. Diversification: Maintain a balanced portfolio across sectors. In India, include public sector undertakings (PSUs) for stability alongside growth companies.
        
        7. Investing During Market Downturns: Market corrections offer buying opportunities. The Indian market has seen several significant corrections (2008, 2020) that rewarded patient investors.
        
        8. Long-Term Perspective: Investment success comes from long-term holding, not short-term trading. Particularly relevant in India where equity investing culture is still developing.
        
        India-specific applications:
        - Look beyond quarterly results in cyclical Indian sectors
        - Consider corporate governance carefully in family-owned businesses
        - Analyze government policy impacts on sectors
        - Account for inflation effects on valuations
        - Be cautious of high-debt companies in interest rate-sensitive environments
        
        Graham's philosophy of disciplined, research-based investing remains highly relevant for Indian value investors.
        """
        
        # Rich Dad Poor Dad
        self.book_content["Rich Dad Poor Dad"] = """
        Rich Dad Poor Dad by Robert Kiyosaki offers financial mindset lessons applicable to the Indian context.
        
        Key insights for Indian investors:
        
        1. Assets vs. Liabilities: Assets put money in your pocket; liabilities take money out. In India, many confuse liabilities (like expensive homes) with assets.
        
        2. Financial Education: The education system doesn't teach financial literacy. Indians need to self-educate on personal finance, taxation, and investing.
        
        3. Work for Learning, Not Just Earning: Develop skills that increase earning potential. For Indian professionals, this means continuous upskilling beyond degrees.
        
        4. Mind Your Own Business: Build assets outside your profession. Indians often rely solely on salary/business income without building investment assets.
        
        5. Tax Efficiency: Understand how taxes work and legal ways to minimize them. In India, use tax-efficient investment vehicles like ELSS, PPF, and NPS.
        
        6. Taking Calculated Risks: Overcome fear and take calculated investment risks. Many Indian investors stick only to fixed deposits due to risk aversion.
        
        7. Pay Yourself First: Invest before spending on expenses. Use SIPs (Systematic Investment Plans) in India to automate this habit.
        
        8. Create Multiple Income Streams: Develop passive income sources beyond your job. Indian investors can consider rental properties, dividend stocks, and business investments.
        
        India-specific applications:
        - Move beyond traditional gold and real estate fixation
        - Utilize mutual funds and direct equity for wealth creation
        - Consider tax-advantaged investment options
        - Build emergency funds to avoid personal loans
        - Start investing early to benefit from compounding
        - Develop financial independence mindset in a society focused on job security
        
        The book's principles of financial independence and asset-building are increasingly relevant as India's economy evolves.
        """
        
        # Value Investing and Behavioral Finance
        self.book_content["Value Investing and Behavioral Finance"] = """
        Value Investing and Behavioral Finance by Parag Parikh provides insights specifically for Indian markets.
        
        Key insights:
        
        1. Behavioral Biases in Indian Markets: Indian investors often exhibit strong herding behavior, overconfidence, and home bias. Recognizing these biases creates opportunities.
        
        2. Value Investing Framework for India: Look for businesses with sustainable competitive advantages, honest management, and reasonable valuations. In India, family-owned businesses require special governance assessment.
        
        3. Market Inefficiencies in India: Indian markets show greater inefficiencies than developed markets, creating more opportunities for value investors.
        
        4. Process Over Outcome: Develop a consistent investment process rather than chasing results. In volatile Indian markets, this discipline is crucial.
        
        5. Contrarian Thinking: Buy when others are fearful; sell when they're greedy. During market panics in India (like in 2008, 2020), contrarians found exceptional value.
        
        6. Avoiding Investment Bubbles: Recognize bubble formations in sectors. India has seen bubbles in infrastructure, real estate, and small/micro-cap stocks.
        
        7. Corporate Governance: In the Indian context, corporate governance is a crucial factor. Analyze related-party transactions, promoter pledging, and accounting practices carefully.
        
        8. Long-Term Equity Investing: Equity investments outperform other asset classes over long periods, despite short-term volatility. This applies to Indian markets despite their higher volatility.
        
        India-specific applications:
        - Analyze government policy impacts on businesses
        - Consider competitive moats in rapidly changing sectors
        - Evaluate family-owned businesses carefully
        - Look beyond headline numbers to cash flows
        - Consider information asymmetry in small/mid-cap space
        - Assess corporate governance rigorously
        
        Parikh's approach combines Graham's value principles with behavioral insights specifically tuned to Indian market realities.
        """
        
        # Add more books as needed
    
    def create_book_vectorstore(self, book_title=None):
        """
        Create a vector store from book content
        
        Args:
            book_title (str): Specific book title, or None for all books
            
        Returns:
            FAISS: Vector store for book content
        """
        if not self.embeddings:
            logger.error("Embeddings model not initialized")
            return None
        
        try:
            # Prepare documents
            docs = []
            
            if book_title and book_title in self.book_content:
                # Single book
                text = self.book_content[book_title]
                docs.append({
                    "text": text,
                    "metadata": {"title": book_title, "source": "book"}
                })
            else:
                # All books
                for title, content in self.book_content.items():
                    docs.append({
                        "text": content,
                        "metadata": {"title": title, "source": "book"}
                    })
            
            # Process documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=RAG_CHUNK_SIZE,
                chunk_overlap=RAG_CHUNK_OVERLAP
            )
            
            processed_docs = []
            for doc in docs:
                splits = text_splitter.split_text(doc["text"])
                for split in splits:
                    processed_docs.append({
                        "page_content": split,
                        "metadata": doc["metadata"]
                    })
            
            # Create vector store
            vectorstore = FAISS.from_texts(
                [doc["page_content"] for doc in processed_docs],
                self.embeddings,
                [doc["metadata"] for doc in processed_docs]
            )
            
            return vectorstore
        
        except Exception as e:
            logger.error(f"Error creating book vector store: {e}")
            return None
    
    def query_books(self, query, vectorstore=None, num_results=3):
        """
        Query book content for relevant information
        
        Args:
            query (str): Query string
            vectorstore: Vector store to query (if None, creates a new one)
            num_results (int): Number of results to return
            
        Returns:
            dict: Relevant book excerpts and sources
        """
        try:
            # Create vector store if not provided
            if not vectorstore:
                vectorstore = self.create_book_vectorstore()
            
            if not vectorstore:
                return {
                    "query": query,
                    "results": [],
                    "error": "Failed to create vector store"
                }
            
            # Search for relevant content
            results = vectorstore.similarity_search_with_score(query, k=num_results)
            
            # Process results
            processed_results = []
            for doc, score in results:
                processed_results.append({
                    "content": doc.page_content,
                    "book": doc.metadata.get("title", "Unknown"),
                    "relevance_score": float(score),
                    "source": "book"
                })
            
            return {
                "query": query,
                "results": processed_results,
                "count": len(processed_results)
            }
        
        except Exception as e:
            logger.error(f"Error querying books: {e}")
            return {
                "query": query,
                "results": [],
                "error": str(e)
            }
    
    def get_financial_advice_from_books(self, question, context=None):
        """
        Get financial advice based on book knowledge and optional context
        
        Args:
            question (str): Financial question
            context (dict): Additional context information
            
        Returns:
            dict: Financial advice with book references
        """
        if not self.llm:
            return {
                "question": question,
                "answer": "LLM not initialized. Please provide a valid API key.",
                "references": []
            }
        
        try:
            # Query books for relevant content
            vectorstore = self.create_book_vectorstore()
            book_results = self.query_books(question, vectorstore, num_results=3)
            
            # Create context for the LLM
            references = book_results.get("results", [])
            
            reference_texts = []
            for ref in references:
                reference_texts.append(f"From '{ref['book']}':\n{ref['content']}")
            
            reference_context = "\n\n".join(reference_texts)
            
            # Add additional context if provided
            additional_context = ""
            if context:
                additional_context = f"\nAdditional context:\n{json.dumps(context, indent=2)}"
            
            # Create prompt
            prompt = f"""
            You are a financial advisor with expertise in Indian markets and personal finance.
            
            Answer the following question using insights from financial books and your knowledge of Indian financial markets.
            
            References from financial books:
            {reference_context}
            {additional_context}
            
            Question: {question}
            
            Provide a comprehensive answer that:
            1. Directly addresses the question
            2. Incorporates relevant insights from the book references
            3. Adapts the advice to the Indian financial context (taxes, regulations, market conditions)
            4. Mentions which books the advice is drawing from
            5. Provides practical, actionable steps if applicable
            
            Answer:
            """
            
            # Get response from LLM
            response = self.llm(prompt)
            
            # Extract book references for citation
            book_citations = []
            for ref in references:
                book_citations.append({
                    "book": ref["book"],
                    "excerpt": ref["content"][:100] + "..." if len(ref["content"]) > 100 else ref["content"]
                })
            
            return {
                "question": question,
                "answer": response,
                "references": book_citations
            }
        
        except Exception as e:
            logger.error(f"Error getting financial advice from books: {e}")
            return {
                "question": question,
                "answer": f"An error occurred: {str(e)}",
                "references": []
            }
    
    def get_book_recommendations(self, financial_goal):
        """
        Get book recommendations based on financial goals
        
        Args:
            financial_goal (str): Financial goal or interest area
            
        Returns:
            dict: Recommended books with reasoning
        """
        try:
            # Map goals to book recommendations
            goal_to_books = {
                "investing": ["The Intelligent Investor", "Value Investing and Behavioral Finance"],
                "personal finance": ["Let's Talk Money", "Rich Dad Poor Dad"],
                "wealth creation": ["Rich Dad Poor Dad", "The Intelligent Investor"],
                "stock market": ["The Intelligent Investor", "Value Investing and Behavioral Finance"],
                "financial planning": ["Let's Talk Money"],
                "mindset": ["Rich Dad Poor Dad"]
            }
            
            # Find the most relevant category
            goal_lower = financial_goal.lower()
            matched_category = None
            
            for category in goal_to_books:
                if category in goal_lower:
                    matched_category = category
                    break
            
            # If no direct match, use LLM to determine best category
            if not matched_category and self.llm:
                prompt = f"""
                Determine which financial category best matches this goal: "{financial_goal}"
                Options:
                - investing
                - personal finance
                - wealth creation
                - stock market
                - financial planning
                - mindset
                
                Return only the single best matching category name from the options, no explanation.
                """
                matched_category = self.llm(prompt).strip().lower()
                
                # Verify the category exists
                if matched_category not in goal_to_books:
                    matched_category = "personal finance"  # Default fallback
            elif not matched_category:
                matched_category = "personal finance"  # Default fallback
            
            # Get recommended books
            recommended_books = goal_to_books.get(matched_category, ["Let's Talk Money"])
            
            # Get book details
            recommendations = []
            for book_title in recommended_books:
                book_info = next((book for book in self.financial_books if book["title"] == book_title), None)
                if book_info:
                    recommendations.append(book_info)
            
            # Get personalized explanation if LLM is available
            explanation = ""
            if self.llm:
                books_str = ", ".join([book["title"] for book in recommendations])
                prompt = f"""
                Explain why these books ({books_str}) are recommended for someone interested in "{financial_goal}".
                Focus on how these books specifically apply to Indian investors and the Indian financial context.
                Keep the explanation under 150 words.
                """
                explanation = self.llm(prompt).strip()
            
            return {
                "goal": financial_goal,
                "category": matched_category,
                "recommendations": recommendations,
                "explanation": explanation
            }
        
        except Exception as e:
            logger.error(f"Error getting book recommendations: {e}")
            return {
                "goal": financial_goal,
                "recommendations": [book for book in self.financial_books[:2]],
                "error": str(e)
            }
