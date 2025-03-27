import sys
import os
import logging
from datetime import datetime, timedelta
import json

# Add the project directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Use direct database connection to avoid circular imports
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

# Configure the database
DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define models directly here to avoid circular imports
class LearningResource(Base):
    """Financial learning resources"""
    __tablename__ = 'learning_resources'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    content = Column(Text, nullable=False)  # Could be text content or embedded links
    resource_type = Column(String(20), nullable=False)  # article, video, quiz, infographic
    topic = Column(String(100), nullable=False, index=True)  # Topic categorization
    subtopic = Column(String(100))  # More specific categorization
    difficulty_level = Column(String(20), nullable=False, default="Beginner")  # Beginner, Intermediate, Advanced
    duration_minutes = Column(Integer, default=5)  # Estimated time to complete
    prerequisites = Column(JSON, default=[])  # List of prerequisite resource IDs
    thumbnail_url = Column(String(500))
    external_url = Column(String(500))  # External resource link
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<LearningResource {self.title}>"

class LearningPath(Base):
    """Organized learning paths for different financial topics"""
    __tablename__ = 'learning_paths'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    target_audience = Column(String(50), nullable=False)  # Beginners, Professionals, etc.
    difficulty_level = Column(String(20), nullable=False)
    estimated_days = Column(Integer, default=30)
    topics_covered = Column(JSON, default=[])  # List of topics
    resource_sequence = Column(JSON, default=[])  # Ordered list of resource IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<LearningPath {self.name}>"

class DailyTip(Base):
    """Daily financial tips for users"""
    __tablename__ = 'daily_tips'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # If NULL, it's a global tip
    tip_text = Column(Text, nullable=False)
    tip_title = Column(String(200), nullable=False)
    tip_category = Column(String(50), nullable=False)  # investing, saving, tax, etc.
    tip_difficulty = Column(String(20), default="Beginner")  # Beginner, Intermediate, Advanced
    is_personalized = Column(Boolean, default=False)
    read = Column(Boolean, default=False)  # Track if user has read this tip
    saved = Column(Boolean, default=False)  # Track if user has saved this tip
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<DailyTip {self.tip_title}>"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def seed_learning_resources():
    """Seed the database with learning resources"""
    logger.info("Seeding learning resources...")
    
    # Check if we already have learning resources
    existing_resources = LearningResource.query.count()
    if existing_resources > 0:
        logger.info(f"Found {existing_resources} existing resources, skipping seed.")
        return
    
    # Beginner Resources
    beginner_resources = [
        {
            'title': 'Understanding the Stock Market Basics',
            'description': 'Learn the fundamentals of how the stock market works and key terminology.',
            'content': """
                <h2>Introduction to the Stock Market</h2>
                <p>The stock market is a place where shares of publicly listed companies are traded. In India, the two main stock exchanges are the National Stock Exchange (NSE) and the Bombay Stock Exchange (BSE).</p>
                
                <h3>Key Concepts</h3>
                <ul>
                    <li><strong>Stocks/Shares</strong>: A unit of ownership in a company.</li>
                    <li><strong>Market Indices</strong>: Indicators that represent a specific segment of the stock market. The most popular indices in India are Sensex and Nifty.</li>
                    <li><strong>Bull Market</strong>: A market condition where prices are rising or expected to rise.</li>
                    <li><strong>Bear Market</strong>: A market condition where prices are falling or expected to fall.</li>
                    <li><strong>Dividend</strong>: A portion of a company's earnings distributed to shareholders.</li>
                </ul>
                
                <h3>How to Start Investing</h3>
                <p>To start investing in the Indian stock market, you need:</p>
                <ol>
                    <li>A PAN card</li>
                    <li>A demat account and trading account (often provided together by brokers)</li>
                    <li>KYC verification</li>
                    <li>Bank account linked to your trading account</li>
                </ol>
                
                <p>Once you have these set up, you can begin investing through your chosen broker's platform.</p>
            """,
            'resource_type': 'article',
            'topic': 'Stock Market Basics',
            'difficulty_level': 'Beginner',
            'duration_minutes': 15
        },
        {
            'title': 'Types of Mutual Funds for New Investors',
            'description': 'Explore the different types of mutual funds available in India and their key characteristics.',
            'content': """
                <h2>Understanding Mutual Funds</h2>
                <p>Mutual funds are investment vehicles that pool money from multiple investors to invest in a diversified portfolio of stocks, bonds, or other securities.</p>
                
                <h3>Types of Mutual Funds in India</h3>
                
                <h4>Based on Asset Class</h4>
                <ul>
                    <li><strong>Equity Funds</strong>: Invest primarily in stocks, offering high growth potential with higher risk.</li>
                    <li><strong>Debt Funds</strong>: Invest in fixed-income securities like bonds and government securities, offering stable returns with lower risk.</li>
                    <li><strong>Hybrid Funds</strong>: Invest in a mix of equity and debt instruments, balancing risk and returns.</li>
                    <li><strong>Money Market Funds</strong>: Invest in short-term, highly liquid instruments, ideal for parking short-term surplus money.</li>
                </ul>
                
                <h4>Based on Investment Objective</h4>
                <ul>
                    <li><strong>Growth Funds</strong>: Focus on capital appreciation over the long term.</li>
                    <li><strong>Income Funds</strong>: Focus on generating regular income for investors.</li>
                    <li><strong>Tax-Saving Funds (ELSS)</strong>: Equity-linked savings schemes that offer tax benefits under Section 80C.</li>
                    <li><strong>Index Funds</strong>: Passively managed funds that track a specific market index like Nifty or Sensex.</li>
                </ul>
                
                <h3>How to Invest in Mutual Funds</h3>
                <p>You can invest in mutual funds through:</p>
                <ol>
                    <li>Direct plans (through the fund house directly)</li>
                    <li>Regular plans (through intermediaries like banks or distributors)</li>
                    <li>Systematic Investment Plans (SIPs) - making regular fixed investments</li>
                    <li>Lump sum investments - investing a larger amount at once</li>
                </ol>
                
                <p>For beginners, starting with SIPs in diversified equity funds or balanced funds is often recommended.</p>
            """,
            'resource_type': 'article',
            'topic': 'Mutual Funds',
            'difficulty_level': 'Beginner',
            'duration_minutes': 20
        },
        {
            'title': 'Basic Risk Management for New Investors',
            'description': 'Learn essential risk management strategies to protect your investments.',
            'content': """
                <h2>Understanding Investment Risk</h2>
                <p>Risk is the possibility of losing some or all of your investment. Managing risk is essential for successful investing.</p>
                
                <h3>Types of Investment Risks</h3>
                <ul>
                    <li><strong>Market Risk</strong>: The risk of investments declining due to market factors.</li>
                    <li><strong>Inflation Risk</strong>: The risk that your investment returns won't keep pace with inflation.</li>
                    <li><strong>Liquidity Risk</strong>: The risk of not being able to sell an investment quickly without loss.</li>
                    <li><strong>Concentration Risk</strong>: The risk of having too much exposure to a single investment or sector.</li>
                </ul>
                
                <h3>Risk Management Strategies for Beginners</h3>
                <ol>
                    <li><strong>Diversification</strong>: Spread your investments across different asset classes, sectors, and geographies.</li>
                    <li><strong>Asset Allocation</strong>: Determine the right mix of stocks, bonds, and other investments based on your goals and risk tolerance.</li>
                    <li><strong>Regular Rebalancing</strong>: Periodically adjust your portfolio to maintain your target asset allocation.</li>
                    <li><strong>Investing for the Long Term</strong>: Longer investment horizons can help smooth out market volatility.</li>
                    <li><strong>Emergency Fund</strong>: Maintain 6-12 months of expenses in easily accessible accounts before investing in markets.</li>
                </ol>
                
                <h3>Determining Your Risk Tolerance</h3>
                <p>Your risk tolerance depends on factors like:</p>
                <ul>
                    <li>Your age and investment horizon</li>
                    <li>Your financial goals and needs</li>
                    <li>Your financial situation and responsibilities</li>
                    <li>Your comfort level with market fluctuations</li>
                </ul>
                
                <p>A common rule of thumb is to subtract your age from 100 to determine the percentage of your portfolio that should be in stocks, with the rest in more conservative investments.</p>
            """,
            'resource_type': 'article',
            'topic': 'Risk Management',
            'difficulty_level': 'Beginner',
            'duration_minutes': 15
        },
        {
            'title': 'Tax Planning Basics for Indian Investors',
            'description': 'Understand the fundamentals of tax planning for your investments in India.',
            'content': """
                <h2>Introduction to Tax Planning</h2>
                <p>Tax planning is the analysis of one's financial situation to ensure maximum tax efficiency. Effective tax planning can help you reduce your tax liability legally.</p>
                
                <h3>Tax-Saving Investment Options in India</h3>
                <ul>
                    <li><strong>Section 80C Investments (₹1.5 lakh limit)</strong>
                        <ul>
                            <li>Equity-Linked Savings Schemes (ELSS)</li>
                            <li>Public Provident Fund (PPF)</li>
                            <li>National Pension System (NPS)</li>
                            <li>Tax-Saving Fixed Deposits</li>
                            <li>Life Insurance Premiums</li>
                        </ul>
                    </li>
                    <li><strong>Additional Deductions</strong>
                        <ul>
                            <li>Section 80D: Health Insurance Premiums (up to ₹25,000 for self and family, additional ₹25,000 for parents)</li>
                            <li>Section 80TTA: Interest income from savings account (up to ₹10,000)</li>
                            <li>Section 24: Home Loan Interest (up to ₹2 lakh for self-occupied property)</li>
                        </ul>
                    </li>
                </ul>
                
                <h3>Tax Treatment of Different Investments</h3>
                <table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>Investment Type</th>
                            <th>Tax on Returns/Gains</th>
                            <th>Tax-saving Benefits</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Equity Mutual Funds</td>
                            <td>LTCG (>1 year): 10% above ₹1 lakh<br>STCG (<1 year): 15%</td>
                            <td>ELSS: Section 80C</td>
                        </tr>
                        <tr>
                            <td>Debt Mutual Funds</td>
                            <td>LTCG (>3 years): 20% with indexation<br>STCG (<3 years): As per income tax slab</td>
                            <td>None</td>
                        </tr>
                        <tr>
                            <td>Fixed Deposits</td>
                            <td>Interest taxed as per income tax slab</td>
                            <td>Tax-saving FDs: Section 80C</td>
                        </tr>
                        <tr>
                            <td>PPF</td>
                            <td>Exempt (EEE category)</td>
                            <td>Section 80C</td>
                        </tr>
                    </tbody>
                </table>
                
                <h3>Tax Planning Strategies for Beginners</h3>
                <ol>
                    <li>Invest in tax-efficient instruments based on your goals and risk profile</li>
                    <li>Consider the lock-in period of tax-saving investments</li>
                    <li>Maximize available deductions under various sections</li>
                    <li>Understand the difference between tax exemptions and tax deductions</li>
                    <li>Maintain proper documentation for all tax-saving investments</li>
                </ol>
                
                <p><strong>Note:</strong> Tax laws are subject to change. Always consult a tax professional for personalized advice.</p>
            """,
            'resource_type': 'article',
            'topic': 'Tax Planning',
            'difficulty_level': 'Beginner',
            'duration_minutes': 25
        }
    ]
    
    # Intermediate Resources
    intermediate_resources = [
        {
            'title': 'Understanding Financial Ratios and Statements',
            'description': 'Learn how to analyze company financial statements and important financial ratios.',
            'content': """
                <h2>Analyzing Financial Statements</h2>
                <p>Financial statements provide crucial information about a company's financial health. The three main financial statements are the Income Statement, Balance Sheet, and Cash Flow Statement.</p>
                
                <h3>Key Financial Ratios</h3>
                
                <h4>Profitability Ratios</h4>
                <ul>
                    <li><strong>Gross Profit Margin</strong> = Gross Profit / Revenue</li>
                    <li><strong>Operating Profit Margin</strong> = Operating Profit / Revenue</li>
                    <li><strong>Net Profit Margin</strong> = Net Profit / Revenue</li>
                    <li><strong>Return on Equity (ROE)</strong> = Net Income / Shareholders' Equity</li>
                    <li><strong>Return on Assets (ROA)</strong> = Net Income / Total Assets</li>
                </ul>
                
                <h4>Liquidity Ratios</h4>
                <ul>
                    <li><strong>Current Ratio</strong> = Current Assets / Current Liabilities</li>
                    <li><strong>Quick Ratio (Acid Test)</strong> = (Current Assets - Inventory) / Current Liabilities</li>
                </ul>
                
                <h4>Solvency Ratios</h4>
                <ul>
                    <li><strong>Debt-to-Equity Ratio</strong> = Total Debt / Shareholders' Equity</li>
                    <li><strong>Interest Coverage Ratio</strong> = EBIT / Interest Expense</li>
                </ul>
                
                <h4>Valuation Ratios</h4>
                <ul>
                    <li><strong>Price-to-Earnings (P/E) Ratio</strong> = Market Price per Share / Earnings per Share</li>
                    <li><strong>Price-to-Book (P/B) Ratio</strong> = Market Price per Share / Book Value per Share</li>
                    <li><strong>Price-to-Sales (P/S) Ratio</strong> = Market Price per Share / Sales per Share</li>
                    <li><strong>Enterprise Value to EBITDA (EV/EBITDA)</strong> = Enterprise Value / EBITDA</li>
                </ul>
                
                <h3>Analyzing Income Statement</h3>
                <p>The Income Statement shows a company's revenues, expenses, and profits over a specific period.</p>
                <p>Key items to analyze:</p>
                <ul>
                    <li>Revenue growth trends</li>
                    <li>Gross, operating, and net profit margins</li>
                    <li>Operating expenses as a percentage of revenue</li>
                    <li>Unusual or one-time items that might distort results</li>
                </ul>
                
                <h3>Analyzing Balance Sheet</h3>
                <p>The Balance Sheet provides a snapshot of a company's assets, liabilities, and shareholders' equity at a specific point in time.</p>
                <p>Key items to analyze:</p>
                <ul>
                    <li>Debt levels and debt-to-equity ratio</li>
                    <li>Working capital (current assets - current liabilities)</li>
                    <li>Asset quality and composition</li>
                    <li>Shareholders' equity growth over time</li>
                </ul>
                
                <h3>Analyzing Cash Flow Statement</h3>
                <p>The Cash Flow Statement shows how changes in balance sheet accounts and income affect cash and cash equivalents.</p>
                <p>Key items to analyze:</p>
                <ul>
                    <li>Operating cash flow vs. net income (quality of earnings)</li>
                    <li>Free cash flow (operating cash flow - capital expenditures)</li>
                    <li>Cash spent on investments and financing activities</li>
                    <li>Sustainable dividend payments</li>
                </ul>
                
                <p>Remember that financial ratios should be compared with industry averages and the company's historical performance for meaningful analysis.</p>
            """,
            'resource_type': 'article',
            'topic': 'Fundamental Analysis',
            'difficulty_level': 'Intermediate',
            'duration_minutes': 30
        },
        {
            'title': 'Asset Allocation Strategies',
            'description': 'Learn how to build a balanced investment portfolio through strategic asset allocation.',
            'content': """
                <h2>Strategic Asset Allocation</h2>
                <p>Asset allocation is the process of dividing your investment portfolio among different asset categories like stocks, bonds, and cash. It's one of the most important decisions you'll make as an investor.</p>
                
                <h3>Importance of Asset Allocation</h3>
                <ul>
                    <li>Studies show that asset allocation determines up to 90% of a portfolio's return variability</li>
                    <li>Proper allocation can reduce overall portfolio risk</li>
                    <li>Different asset classes perform differently under various market conditions</li>
                </ul>
                
                <h3>Common Asset Classes</h3>
                <ul>
                    <li><strong>Equity (Stocks)</strong>: Higher risk, higher potential returns</li>
                    <li><strong>Fixed Income (Bonds)</strong>: Lower risk, more stable returns</li>
                    <li><strong>Cash & Equivalents</strong>: Lowest risk, lowest returns</li>
                    <li><strong>Alternative Investments</strong>: Real estate, commodities, private equity</li>
                </ul>
                
                <h3>Factors Influencing Asset Allocation</h3>
                <ol>
                    <li><strong>Investment Goals</strong>: What are you investing for? (Retirement, home purchase, education)</li>
                    <li><strong>Time Horizon</strong>: How long until you need the money?</li>
                    <li><strong>Risk Tolerance</strong>: How comfortable are you with volatility?</li>
                    <li><strong>Financial Situation</strong>: Your income, expenses, existing assets, and liabilities</li>
                    <li><strong>Market Conditions</strong>: Current and expected economic environment</li>
                </ol>
                
                <h3>Asset Allocation Models</h3>
                
                <h4>Age-Based Allocation</h4>
                <p>A simple rule: Subtract your age from 100 to determine the percentage of your portfolio to allocate to stocks.</p>
                <ul>
                    <li>Example: A 30-year-old would have 70% in stocks, 30% in bonds</li>
                    <li>A 60-year-old would have 40% in stocks, 60% in bonds</li>
                </ul>
                
                <h4>Goal-Based Allocation</h4>
                <p>Different allocations for different financial goals:</p>
                <ul>
                    <li><strong>Short-term goals</strong> (0-3 years): Conservative allocation (20% stocks, 80% bonds/cash)</li>
                    <li><strong>Medium-term goals</strong> (3-10 years): Moderate allocation (50% stocks, 50% bonds)</li>
                    <li><strong>Long-term goals</strong> (10+ years): Aggressive allocation (80% stocks, 20% bonds)</li>
                </ul>
                
                <h4>Three-Fund Portfolio</h4>
                <p>A simple yet effective approach:</p>
                <ul>
                    <li>Domestic equity index fund</li>
                    <li>International equity index fund</li>
                    <li>Bond index fund</li>
                </ul>
                
                <h3>Rebalancing Your Portfolio</h3>
                <p>Over time, some assets will perform better than others, causing your portfolio to drift from your target allocation. Rebalancing involves adjusting your portfolio back to your target allocation.</p>
                
                <p>Rebalancing methods:</p>
                <ul>
                    <li><strong>Calendar rebalancing</strong>: Rebalance at set intervals (quarterly, annually)</li>
                    <li><strong>Percentage-of-portfolio rebalancing</strong>: Rebalance when an asset class deviates by a predetermined percentage (e.g., 5%)</li>
                    <li><strong>Tactical rebalancing</strong>: Adjust allocation based on market conditions</li>
                </ul>
                
                <p>Remember that rebalancing may have tax implications, so consider using tax-advantaged accounts for frequent rebalancing.</p>
            """,
            'resource_type': 'article',
            'topic': 'Portfolio Management',
            'difficulty_level': 'Intermediate',
            'duration_minutes': 25
        }
    ]
    
    # Advanced Resources
    advanced_resources = [
        {
            'title': 'Options Trading Strategies for Income Generation',
            'description': 'Learn advanced options strategies to generate income from your portfolio.',
            'content': """
                <h2>Options Trading for Income</h2>
                <p>Options contracts offer unique opportunities for generating income beyond traditional buy-and-hold investing. This guide explores advanced options strategies specifically for income generation.</p>
                
                <div class="alert alert-warning">
                    <strong>Warning:</strong> Options trading involves significant risk and is not suitable for all investors. Before trading options, understand the strategies thoroughly and consider consulting a financial advisor.
                </div>
                
                <h3>Covered Call Strategy</h3>
                <p>A covered call involves holding a long position in an asset and selling call options on that same asset.</p>
                
                <h4>How it works:</h4>
                <ol>
                    <li>Own 100 shares of a stock</li>
                    <li>Sell a call option contract (representing 100 shares) against your holding</li>
                    <li>Collect the premium immediately</li>
                </ol>
                
                <h4>Income potential:</h4>
                <ul>
                    <li>Regular income from option premiums</li>
                    <li>Typically generates 1-2% monthly returns (depending on volatility)</li>
                    <li>Can enhance returns on stocks you plan to hold long-term</li>
                </ul>
                
                <h4>Risks:</h4>
                <ul>
                    <li>Limited upside potential (capped at strike price)</li>
                    <li>Still exposed to downside risk of the underlying stock</li>
                </ul>
                
                <h3>Cash-Secured Put Strategy</h3>
                <p>A cash-secured put involves selling a put option while maintaining enough cash to purchase the stock if the option is exercised.</p>
                
                <h4>How it works:</h4>
                <ol>
                    <li>Set aside cash equivalent to purchase 100 shares at the strike price</li>
                    <li>Sell a put option contract</li>
                    <li>Collect the premium immediately</li>
                </ol>
                
                <h4>Income potential:</h4>
                <ul>
                    <li>Similar return profile to covered calls</li>
                    <li>Method to potentially acquire stocks at a discount</li>
                    <li>Works well in sideways or slightly bullish markets</li>
                </ul>
                
                <h4>Risks:</h4>
                <ul>
                    <li>Obligation to buy shares at strike price if assigned</li>
                    <li>Potential opportunity cost if cash is set aside</li>
                </ul>
                
                <h3>Iron Condor Strategy</h3>
                <p>An iron condor is a market-neutral options strategy that involves selling an out-of-the-money put spread and an out-of-the-money call spread.</p>
                
                <h4>How it works:</h4>
                <ol>
                    <li>Sell an out-of-the-money put option</li>
                    <li>Buy a further out-of-the-money put option</li>
                    <li>Sell an out-of-the-money call option</li>
                    <li>Buy a further out-of-the-money call option</li>
                </ol>
                
                <h4>Income potential:</h4>
                <ul>
                    <li>Profit when the underlying asset remains between your short put and short call strikes</li>
                    <li>Maximum profit is the net premium received</li>
                    <li>Works best in low-volatility, range-bound markets</li>
                </ul>
                
                <h4>Risks:</h4>
                <ul>
                    <li>Limited but defined risk (difference between strikes minus premium received)</li>
                    <li>Significant price movements in either direction can lead to losses</li>
                </ul>
                
                <h3>Implementation Tips</h3>
                <ol>
                    <li><strong>Choose the right underlyings</strong>: Select stocks or ETFs with moderate volatility and sufficient liquidity in their options markets</li>
                    <li><strong>Select appropriate strikes</strong>: For covered calls, choose strikes above your cost basis; for puts, choose strikes where you'd be comfortable owning the stock</li>
                    <li><strong>Time decay</strong>: Options lose value as they approach expiration (theta decay), which benefits the option seller</li>
                    <li><strong>Manage risk</strong>: Consider closing positions early when you've captured 50-75% of the maximum profit</li>
                    <li><strong>Watch for earnings and dividends</strong>: Be cautious when selling options through events that could cause significant price movements</li>
                </ol>
                
                <h3>Taxation Considerations</h3>
                <p>In India, options trading is generally considered non-speculative business income. Keep detailed records of all trades for tax purposes and consult a tax professional for guidance on your specific situation.</p>
            """,
            'resource_type': 'article',
            'topic': 'Advanced Trading',
            'difficulty_level': 'Advanced',
            'duration_minutes': 35
        }
    ]
    
    # Combine all resources
    all_resources = beginner_resources + intermediate_resources + advanced_resources
    
    # Add resources to database
    for resource_data in all_resources:
        resource = LearningResource(**resource_data)
        db.session.add(resource)
    
    try:
        db.session.commit()
        logger.info(f"Added {len(all_resources)} learning resources")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error seeding learning resources: {e}")
        raise

def seed_learning_paths():
    """Seed the database with learning paths"""
    logger.info("Seeding learning paths...")
    
    # Check if we already have learning paths
    existing_paths = LearningPath.query.count()
    if existing_paths > 0:
        logger.info(f"Found {existing_paths} existing paths, skipping seed.")
        return
    
    # Get resources for paths
    stock_basics = LearningResource.query.filter_by(topic='Stock Market Basics', difficulty_level='Beginner').first()
    mutual_funds = LearningResource.query.filter_by(topic='Mutual Funds', difficulty_level='Beginner').first()
    tax_planning = LearningResource.query.filter_by(topic='Tax Planning', difficulty_level='Beginner').first()
    risk_management = LearningResource.query.filter_by(topic='Risk Management', difficulty_level='Beginner').first()
    
    # Intermediate resources
    fundamental_analysis = LearningResource.query.filter_by(topic='Fundamental Analysis', difficulty_level='Intermediate').first()
    portfolio_management = LearningResource.query.filter_by(topic='Portfolio Management', difficulty_level='Intermediate').first()
    
    # Advanced resources
    advanced_trading = LearningResource.query.filter_by(topic='Advanced Trading', difficulty_level='Advanced').first()
    
    # Get resource IDs (safely)
    resource_ids = []
    if stock_basics:
        resource_ids.append(stock_basics.id)
    if mutual_funds:
        resource_ids.append(mutual_funds.id)
    if risk_management:
        resource_ids.append(risk_management.id)
    if tax_planning:
        resource_ids.append(tax_planning.id)
    
    intermediate_ids = []
    if fundamental_analysis:
        intermediate_ids.append(fundamental_analysis.id)
    if portfolio_management:
        intermediate_ids.append(portfolio_management.id)
    # Add beginner resources to intermediate path too
    intermediate_ids.extend(resource_ids)
    
    advanced_ids = []
    if advanced_trading:
        advanced_ids.append(advanced_trading.id)
    # Add some intermediate resources to advanced path
    if fundamental_analysis:
        advanced_ids.append(fundamental_analysis.id)
    if portfolio_management:
        advanced_ids.append(portfolio_management.id)
    
    # Create learning paths
    beginner_path = LearningPath(
        name="Investment Basics",
        description="A comprehensive introduction to investing in the Indian market, covering the fundamentals that every new investor should know.",
        target_audience="New Investors",
        difficulty_level="Beginner",
        estimated_days=15,
        topics_covered=["Stock Market Basics", "Mutual Funds", "Risk Management", "Tax Planning"],
        resource_sequence=resource_ids
    )
    
    intermediate_path = LearningPath(
        name="Intermediate Investing",
        description="Build on your investing knowledge with more advanced concepts, analysis techniques, and portfolio strategies.",
        target_audience="Investors with Basic Knowledge",
        difficulty_level="Intermediate",
        estimated_days=20,
        topics_covered=["Fundamental Analysis", "Portfolio Management", "Stock Market Basics", "Mutual Funds"],
        resource_sequence=intermediate_ids
    )
    
    advanced_path = LearningPath(
        name="Advanced Trading Strategies",
        description="Master sophisticated trading and investment strategies for experienced investors looking to optimize returns.",
        target_audience="Experienced Investors",
        difficulty_level="Advanced",
        estimated_days=25,
        topics_covered=["Advanced Trading", "Fundamental Analysis", "Portfolio Management"],
        resource_sequence=advanced_ids
    )
    
    db.session.add_all([beginner_path, intermediate_path, advanced_path])
    
    try:
        db.session.commit()
        logger.info("Added 3 learning paths")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error seeding learning paths: {e}")
        raise

def seed_daily_tips():
    """Seed the database with daily tips"""
    logger.info("Seeding daily tips...")
    
    # Check if we already have daily tips
    existing_tips = DailyTip.query.count()
    if existing_tips > 0:
        logger.info(f"Found {existing_tips} existing tips, skipping seed.")
        return
    
    # General tips (user_id is None, meaning they're global)
    general_tips = [
        {
            'tip_title': 'Start With a Small Amount',
            'tip_text': 'Begin investing with a small amount that you\'re comfortable with. As you gain confidence and understanding, you can gradually increase your investment.',
            'tip_category': 'investing',
            'tip_difficulty': 'Beginner',
            'is_personalized': False
        },
        {
            'tip_title': 'Don\'t Try to Time the Market',
            'tip_text': 'Instead of trying to time market highs and lows, consider a systematic investment plan (SIP) to average out your purchase cost over time.',
            'tip_category': 'investing',
            'tip_difficulty': 'Beginner',
            'is_personalized': False
        },
        {
            'tip_title': 'Build an Emergency Fund First',
            'tip_text': 'Before you start investing for long-term goals, make sure you have an emergency fund covering 3-6 months of expenses in liquid instruments.',
            'tip_category': 'personal finance',
            'tip_difficulty': 'Beginner',
            'is_personalized': False
        },
        {
            'tip_title': 'Understand the Power of Compounding',
            'tip_text': 'Starting early, even with small amounts, can lead to significant wealth over time thanks to compounding. An investment of ₹10,000 with a 12% annual return would grow to nearly ₹1 lakh in 20 years.',
            'tip_category': 'investing',
            'tip_difficulty': 'Beginner',
            'is_personalized': False
        },
        {
            'tip_title': 'Check Your Asset Allocation Regularly',
            'tip_text': 'Review your asset allocation at least once a year and rebalance if needed to maintain your desired risk level as market conditions change.',
            'tip_category': 'portfolio',
            'tip_difficulty': 'Intermediate',
            'is_personalized': False
        },
        {
            'tip_title': 'Look Beyond Past Performance',
            'tip_text': 'While historical returns are important, they don\'t guarantee future performance. Evaluate investments based on fundamentals, management quality, and future prospects.',
            'tip_category': 'investing',
            'tip_difficulty': 'Intermediate',
            'is_personalized': False
        },
        {
            'tip_title': 'Know the Tax Implications',
            'tip_text': 'Understand how different investments are taxed. For example, equity funds held for more than a year have a 10% LTCG tax on gains exceeding ₹1 lakh.',
            'tip_category': 'tax',
            'tip_difficulty': 'Intermediate',
            'is_personalized': False
        },
        {
            'tip_title': 'Use Index Funds for Core Holdings',
            'tip_text': 'Low-cost index funds can form the core of your portfolio, providing broad market exposure with minimal expense ratios.',
            'tip_category': 'investing',
            'tip_difficulty': 'Advanced',
            'is_personalized': False
        },
        {
            'tip_title': 'Consider Gold as a Portfolio Diversifier',
            'tip_text': 'Gold often moves differently from stocks and bonds, making it a useful diversifier. Consider allocating 5-10% of your portfolio to gold via sovereign gold bonds or gold ETFs.',
            'tip_category': 'portfolio',
            'tip_difficulty': 'Advanced',
            'is_personalized': False
        },
        {
            'tip_title': 'Monitor Your Investment Costs',
            'tip_text': 'Pay attention to expense ratios, transaction fees, and other costs that can significantly impact your long-term returns.',
            'tip_category': 'investing',
            'tip_difficulty': 'Advanced',
            'is_personalized': False
        }
    ]
    
    # Add tips to database
    for tip_data in general_tips:
        tip = DailyTip(**tip_data)
        db.session.add(tip)
    
    try:
        db.session.commit()
        logger.info(f"Added {len(general_tips)} daily tips")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error seeding daily tips: {e}")
        raise

def run():
    """Main function to seed the database"""
    logger.info("Starting database seeding...")
    
    # Create a database session
    session = SessionLocal()
    
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(engine)
        
        # Check if we already have learning resources
        lr_count = session.query(LearningResource).count()
        if lr_count > 0:
            logger.info(f"Found {lr_count} existing resources, skipping seed.")
        else:
            # Beginner Resources
            for resource_data in beginner_resources:
                resource = LearningResource(**resource_data)
                session.add(resource)
            
            # Intermediate Resources
            for resource_data in intermediate_resources:
                resource = LearningResource(**resource_data)
                session.add(resource)
            
            # Advanced Resources
            for resource_data in advanced_resources:
                resource = LearningResource(**resource_data)
                session.add(resource)
                
            session.commit()
            logger.info(f"Added {len(beginner_resources) + len(intermediate_resources) + len(advanced_resources)} learning resources")
        
        # Check if we already have learning paths
        lp_count = session.query(LearningPath).count()
        if lp_count > 0:
            logger.info(f"Found {lp_count} existing learning paths, skipping seed.")
        else:
            # Get resources for paths
            stock_basics = session.query(LearningResource).filter_by(topic='Stock Market Basics', difficulty_level='Beginner').first()
            mutual_funds = session.query(LearningResource).filter_by(topic='Mutual Funds', difficulty_level='Beginner').first()
            tax_planning = session.query(LearningResource).filter_by(topic='Tax Planning', difficulty_level='Beginner').first()
            risk_management = session.query(LearningResource).filter_by(topic='Risk Management', difficulty_level='Beginner').first()
            
            # Intermediate resources
            fundamental_analysis = session.query(LearningResource).filter_by(topic='Fundamental Analysis', difficulty_level='Intermediate').first()
            portfolio_management = session.query(LearningResource).filter_by(topic='Portfolio Management', difficulty_level='Intermediate').first()
            
            # Advanced resources
            advanced_trading = session.query(LearningResource).filter_by(topic='Advanced Trading', difficulty_level='Advanced').first()
            
            # Get resource IDs (safely)
            resource_ids = []
            if stock_basics:
                resource_ids.append(stock_basics.id)
            if mutual_funds:
                resource_ids.append(mutual_funds.id)
            if risk_management:
                resource_ids.append(risk_management.id)
            if tax_planning:
                resource_ids.append(tax_planning.id)
            
            intermediate_ids = []
            if fundamental_analysis:
                intermediate_ids.append(fundamental_analysis.id)
            if portfolio_management:
                intermediate_ids.append(portfolio_management.id)
            # Add beginner resources to intermediate path too
            intermediate_ids.extend(resource_ids)
            
            advanced_ids = []
            if advanced_trading:
                advanced_ids.append(advanced_trading.id)
            # Add some intermediate resources to advanced path
            if fundamental_analysis:
                advanced_ids.append(fundamental_analysis.id)
            if portfolio_management:
                advanced_ids.append(portfolio_management.id)
            
            # Create learning paths
            beginner_path = LearningPath(
                name="Investment Basics",
                description="A comprehensive introduction to investing in the Indian market, covering the fundamentals that every new investor should know.",
                target_audience="New Investors",
                difficulty_level="Beginner",
                estimated_days=15,
                topics_covered=["Stock Market Basics", "Mutual Funds", "Risk Management", "Tax Planning"],
                resource_sequence=resource_ids
            )
            
            intermediate_path = LearningPath(
                name="Intermediate Investing",
                description="Build on your investing knowledge with more advanced concepts, analysis techniques, and portfolio strategies.",
                target_audience="Investors with Basic Knowledge",
                difficulty_level="Intermediate",
                estimated_days=20,
                topics_covered=["Fundamental Analysis", "Portfolio Management", "Stock Market Basics", "Mutual Funds"],
                resource_sequence=intermediate_ids
            )
            
            advanced_path = LearningPath(
                name="Advanced Trading Strategies",
                description="Master sophisticated trading and investment strategies for experienced investors looking to optimize returns.",
                target_audience="Experienced Investors",
                difficulty_level="Advanced",
                estimated_days=25,
                topics_covered=["Advanced Trading", "Fundamental Analysis", "Portfolio Management"],
                resource_sequence=advanced_ids
            )
            
            session.add_all([beginner_path, intermediate_path, advanced_path])
            session.commit()
            logger.info("Added 3 learning paths")
        
        # Check if we already have daily tips
        tip_count = session.query(DailyTip).count()
        if tip_count > 0:
            logger.info(f"Found {tip_count} existing tips, skipping seed.")
        else:
            # Add tips to database
            for tip_data in general_tips:
                tip = DailyTip(**tip_data)
                session.add(tip)
            
            session.commit()
            logger.info(f"Added {len(general_tips)} daily tips")
        
        logger.info("Database seeding completed successfully!")
    except Exception as e:
        session.rollback()
        logger.error(f"Error seeding database: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    run()