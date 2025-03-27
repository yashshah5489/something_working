import sys
import logging
from datetime import datetime
from app import app, db
from models import LearningResource, LearningPath, DailyTip

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
    
    # Create beginner resources
    resources = [
        LearningResource(
            title="Understanding the Stock Market Basics",
            description="Learn the fundamentals of how the stock market works and key terminology.",
            content="""
                <h2>Introduction to the Stock Market</h2>
                <p>The stock market is a place where shares of publicly listed companies are traded. In India, the two main stock exchanges are the National Stock Exchange (NSE) and the Bombay Stock Exchange (BSE).</p>
                
                <h3>Key Concepts</h3>
                <ul>
                    <li><strong>Stocks/Shares</strong>: A unit of ownership in a company.</li>
                    <li><strong>Market Indices</strong>: Indicators that represent a specific segment of the stock market. The most popular indices in India are Sensex and Nifty.</li>
                    <li><strong>Bull Market</strong>: A market condition where prices are rising or expected to rise.</li>
                    <li><strong>Bear Market</strong>: A market condition where prices are falling or expected to fall.</li>
                    <li><strong>Dividend</strong>: A portion of a company\'s earnings distributed to shareholders.</li>
                </ul>
            """,
            resource_type="article",
            topic="Stock Market Basics",
            difficulty_level="Beginner",
            duration_minutes=15
        ),
        LearningResource(
            title="Types of Mutual Funds for New Investors",
            description="Explore the different types of mutual funds available in India and their key characteristics.",
            content="""
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
            """,
            resource_type="article",
            topic="Mutual Funds",
            difficulty_level="Beginner",
            duration_minutes=20
        ),
        LearningResource(
            title="Financial Ratios for Investors",
            description="Learn how to interpret key financial ratios to evaluate companies.",
            content="""
                <h2>Understanding Financial Ratios</h2>
                <p>Financial ratios help investors evaluate a company's performance and financial health.</p>
                
                <h3>Profitability Ratios</h3>
                <ul>
                    <li><strong>ROE</strong>: Return on Equity shows how efficiently a company uses shareholders' investments.</li>
                    <li><strong>Profit Margin</strong>: Indicates how much of each rupee of revenue is kept as profit.</li>
                </ul>
                
                <h3>Valuation Ratios</h3>
                <ul>
                    <li><strong>P/E Ratio</strong>: Price-to-Earnings ratio compares a company's share price to its earnings per share.</li>
                    <li><strong>P/B Ratio</strong>: Price-to-Book ratio compares a company's market value to its book value.</li>
                </ul>
            """,
            resource_type="article",
            topic="Fundamental Analysis",
            difficulty_level="Intermediate",
            duration_minutes=25
        ),
        LearningResource(
            title="Options Trading Basics",
            description="An introduction to options trading strategies for experienced investors.",
            content="""
                <h2>Understanding Options</h2>
                <p>Options are financial derivatives that give the buyer the right to buy or sell an asset at a specified price within a specific time period.</p>
                
                <h3>Types of Options</h3>
                <ul>
                    <li><strong>Call Options</strong>: Give the right to buy an asset at a specified price.</li>
                    <li><strong>Put Options</strong>: Give the right to sell an asset at a specified price.</li>
                </ul>
                
                <h3>Basic Strategies</h3>
                <ul>
                    <li><strong>Covered Call</strong>: Selling call options on stocks you already own.</li>
                    <li><strong>Protective Put</strong>: Buying put options to protect against downside risk.</li>
                </ul>
            """,
            resource_type="article",
            topic="Advanced Trading",
            difficulty_level="Advanced",
            duration_minutes=30
        )
    ]
    
    # Add resources to database
    for resource in resources:
        db.session.add(resource)
    
    try:
        db.session.commit()
        logger.info(f"Added {len(resources)} learning resources")
        return resources
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error seeding learning resources: {e}")
        raise

def seed_learning_paths(resources):
    """Seed the database with learning paths"""
    logger.info("Seeding learning paths...")
    
    # Check if we already have learning paths
    existing_paths = LearningPath.query.count()
    if existing_paths > 0:
        logger.info(f"Found {existing_paths} existing paths, skipping seed.")
        return
    
    # Get resources by topic and level
    beginner_resources = []
    intermediate_resources = []
    advanced_resources = []
    
    for resource in resources:
        if resource.difficulty_level == "Beginner":
            beginner_resources.append(resource.id)
        elif resource.difficulty_level == "Intermediate":
            intermediate_resources.append(resource.id)
        elif resource.difficulty_level == "Advanced":
            advanced_resources.append(resource.id)
    
    # Create learning paths
    paths = [
        LearningPath(
            name="Investment Basics",
            description="A comprehensive introduction to investing in the Indian market.",
            target_audience="New Investors",
            difficulty_level="Beginner",
            estimated_days=15,
            topics_covered=["Stock Market Basics", "Mutual Funds"],
            resource_sequence=beginner_resources
        ),
        LearningPath(
            name="Intermediate Investing",
            description="Build on your investing knowledge with more advanced concepts.",
            target_audience="Experienced Investors",
            difficulty_level="Intermediate",
            estimated_days=20,
            topics_covered=["Fundamental Analysis"],
            resource_sequence=intermediate_resources + beginner_resources[:1]  # Add first beginner resource too
        ),
        LearningPath(
            name="Advanced Trading",
            description="Master sophisticated trading strategies for experienced investors.",
            target_audience="Professional Investors",
            difficulty_level="Advanced",
            estimated_days=25,
            topics_covered=["Advanced Trading"],
            resource_sequence=advanced_resources + intermediate_resources  # Include intermediate content too
        )
    ]
    
    # Add paths to database
    for path in paths:
        db.session.add(path)
    
    try:
        db.session.commit()
        logger.info(f"Added {len(paths)} learning paths")
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
    
    # Create tips
    tips = [
        DailyTip(
            tip_title="Start With a Small Amount",
            tip_text="Begin investing with a small amount that you\'re comfortable with. As you gain confidence, gradually increase your investment.",
            tip_category="investing",
            tip_difficulty="Beginner",
            is_personalized=False
        ),
        DailyTip(
            tip_title="Don\'t Try to Time the Market",
            tip_text="Instead of trying to time market highs and lows, consider a systematic investment plan (SIP) to average out your purchase cost over time.",
            tip_category="investing",
            tip_difficulty="Beginner",
            is_personalized=False
        ),
        DailyTip(
            tip_title="Build an Emergency Fund First",
            tip_text="Before investing for long-term goals, make sure you have an emergency fund covering 3-6 months of expenses.",
            tip_category="personal finance",
            tip_difficulty="Beginner",
            is_personalized=False
        ),
        DailyTip(
            tip_title="Look Beyond Past Performance",
            tip_text="While historical returns are important, they don\'t guarantee future performance. Evaluate investments based on fundamentals.",
            tip_category="investing",
            tip_difficulty="Intermediate",
            is_personalized=False
        ),
        DailyTip(
            tip_title="Know the Tax Implications",
            tip_text="Understand how different investments are taxed. For example, equity funds held for more than a year have a 10% LTCG tax on gains exceeding ₹1 lakh.",
            tip_category="tax",
            tip_difficulty="Intermediate",
            is_personalized=False
        )
    ]
    
    # Add tips to database
    for tip in tips:
        db.session.add(tip)
    
    try:
        db.session.commit()
        logger.info(f"Added {len(tips)} daily tips")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error seeding daily tips: {e}")
        raise

def run():
    """Main function to seed the database"""
    logger.info("Starting database seeding...")
    
    with app.app_context():
        # Seed the database in order
        resources = seed_learning_resources()
        if resources:
            seed_learning_paths(resources)
        seed_daily_tips()
    
    logger.info("Database seeding completed successfully!")

if __name__ == "__main__":
    run()