import logging
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from services.db_service import db_service
from config import INDIAN_STOCK_EXCHANGES, DEFAULT_STOCK_EXCHANGE

logger = logging.getLogger(__name__)

class StockService:
    """
    Service for retrieving and processing stock data from Indian markets
    using Yahoo Finance API
    """
    def __init__(self):
        self.exchanges = INDIAN_STOCK_EXCHANGES
        self.default_exchange = DEFAULT_STOCK_EXCHANGE
        self.stock_sectors = {
            # Map of some common NSE stocks to their sectors
            "RELIANCE": "Oil & Gas",
            "TCS": "Information Technology",
            "HDFCBANK": "Banking",
            "INFY": "Information Technology",
            "ICICIBANK": "Banking",
            "HINDUNILVR": "FMCG",
            "SBIN": "Banking",
            "BAJFINANCE": "Financial Services",
            "BHARTIARTL": "Telecom",
            "KOTAKBANK": "Banking",
            "WIPRO": "Information Technology",
            "LT": "Construction",
            "HCLTECH": "Information Technology",
            "ASIANPAINT": "Paints",
            "AXISBANK": "Banking",
            "SUNPHARMA": "Pharmaceuticals",
            "MARUTI": "Automobiles",
            "ITC": "FMCG",
            "ONGC": "Oil & Gas",
            "NTPC": "Power"
        }

    def get_stock_data(self, symbol, exchange=None):
        """
        Retrieve current stock data for a given symbol
        """
        try:
            exchange = exchange or self.default_exchange
            
            # Format the symbol for Yahoo Finance
            yf_symbol = self._format_symbol_for_yf(symbol, exchange)
            
            # Check if we have recent data in PostgreSQL
            cached_data = db_service.get_stock_data(symbol, exchange)
            if cached_data and hasattr(cached_data, 'last_updated'):
                # If data is less than 15 minutes old, use it
                last_updated = cached_data.last_updated
                if isinstance(last_updated, str):
                    last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                
                if datetime.utcnow() - last_updated < timedelta(minutes=15):
                    return cached_data
            
            # Get fresh data from Yahoo Finance
            stock = yf.Ticker(yf_symbol)
            info = stock.info
            
            if not info:
                logger.warning(f"No data found for {symbol} on {exchange}")
                return None
            
            # Get sector or use default if not found
            sector = self.stock_sectors.get(symbol, "Miscellaneous")
            
            # Extract the relevant data
            stock_data = {
                "symbol": symbol,
                "exchange": exchange,
                "name": info.get("shortName", symbol),
                "sector": sector,
                "current_price": info.get("currentPrice", info.get("regularMarketPrice")),
                "day_change": info.get("regularMarketChangePercent"),
                "volume": info.get("regularMarketVolume"),
                "high_52week": info.get("fiftyTwoWeekHigh"),
                "low_52week": info.get("fiftyTwoWeekLow"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "dividend_yield": info.get("dividendYield"),
                "last_updated": datetime.utcnow()
            }
            
            # Save to PostgreSQL
            db_service.save_stock_data(stock_data)
            
            return stock_data
        
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            return None

    def get_historical_data(self, symbol, exchange=None, period="1mo"):
        """
        Get historical stock data
        period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        """
        try:
            exchange = exchange or self.default_exchange
            yf_symbol = self._format_symbol_for_yf(symbol, exchange)
            
            stock = yf.Ticker(yf_symbol)
            hist = stock.history(period=period)
            
            # Convert to list of dictionaries for easier use
            result = []
            for index, row in hist.iterrows():
                result.append({
                    "date": index.strftime('%Y-%m-%d'),
                    "open": row["Open"],
                    "high": row["High"],
                    "low": row["Low"],
                    "close": row["Close"],
                    "volume": row["Volume"]
                })
            
            return result
        
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return []

    def get_trending_stocks(self, exchange=None, limit=10):
        """
        Get trending stocks (top gainers and losers) using Yahoo Finance
        """
        try:
            exchange = exchange or self.default_exchange
            gainers = []
            losers = []
            
            # Check if we have fresh data in the database
            db_trending = db_service.get_trending_stocks(limit=limit)
            if db_trending["gainers"] and db_trending["losers"]:
                # If the database has data that's fresh, use it
                first_stock = db_trending["gainers"][0] if db_trending["gainers"] else None
                if first_stock and hasattr(first_stock, 'last_updated'):
                    last_updated = first_stock.last_updated
                    if isinstance(last_updated, str):
                        last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                    
                    if datetime.utcnow() - last_updated < timedelta(minutes=30):
                        return db_trending
            
            # Otherwise, fetch fresh data from Yahoo Finance
            # Use key Indian stock indices for NIFTY/BSE 
            if exchange == "NSE":
                index_symbol = "^NSEI"  # NIFTY 50
            else:
                index_symbol = "^BSESN"  # BSE SENSEX
            
            # Get the top components of the index
            popular_stocks = [
                "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
                "HINDUNILVR", "SBIN", "BAJFINANCE", "ITC", "KOTAKBANK",
                "BHARTIARTL", "ASIANPAINT", "MARUTI", "AXISBANK", "WIPRO",
                "NESTLEIND", "TITAN", "TECHM", "ULTRACEMCO", "ADANIPORTS"
            ]
            
            # Get current data for all stocks in parallel using batch processing
            # Format symbols for YF
            yf_symbols = [self._format_symbol_for_yf(symbol, exchange) for symbol in popular_stocks]
            
            # Use Yahoo Finance's multiple ticker fetch capability
            data = yf.download(
                tickers=yf_symbols,
                period="2d",  # Get 2 days to calculate day change
                group_by="ticker",
                auto_adjust=True,
                threads=True
            )
            
            # Process the data for each stock
            for i, symbol in enumerate(popular_stocks):
                yf_symbol = yf_symbols[i]
                
                try:
                    # Get stock data from batch request
                    if len(popular_stocks) > 1:
                        stock_data = data[yf_symbol]
                    else:
                        stock_data = data  # For single ticker, data is not nested
                    
                    if stock_data.empty:
                        continue
                    
                    # Calculate day change percentage
                    if len(stock_data) >= 2:
                        today_close = stock_data['Close'].iloc[-1]
                        prev_close = stock_data['Close'].iloc[-2]
                        day_change_pct = ((today_close - prev_close) / prev_close) * 100
                    else:
                        day_change_pct = 0
                    
                    # Get additional info for the stock
                    ticker_info = yf.Ticker(yf_symbol).info
                    
                    # Create stock data object
                    stock_info = {
                        "symbol": symbol,
                        "exchange": exchange,
                        "name": ticker_info.get("shortName", symbol),
                        "sector": self.stock_sectors.get(symbol, "Miscellaneous"),
                        "current_price": stock_data['Close'].iloc[-1],
                        "day_change": day_change_pct,
                        "volume": stock_data['Volume'].iloc[-1],
                        "high_52week": ticker_info.get("fiftyTwoWeekHigh"),
                        "low_52week": ticker_info.get("fiftyTwoWeekLow"),
                        "last_updated": datetime.utcnow()
                    }
                    
                    # Save to PostgreSQL
                    db_service.save_stock_data(stock_info)
                    
                    # Categorize as gainer or loser
                    if day_change_pct > 0:
                        gainers.append(stock_info)
                    else:
                        losers.append(stock_info)
                        
                except Exception as e:
                    logger.warning(f"Error processing stock {symbol}: {e}")
                    continue
            
            # Sort by day_change
            gainers.sort(key=lambda x: x.get("day_change", 0) or 0, reverse=True)
            losers.sort(key=lambda x: x.get("day_change", 0) or 0)
            
            # Limit to requested size
            gainers_limit = min(len(gainers), limit // 2)
            losers_limit = min(len(losers), limit - gainers_limit)
            
            trending = {
                "gainers": gainers[:gainers_limit],
                "losers": losers[:losers_limit]
            }
            
            return trending
        
        except Exception as e:
            logger.error(f"Error fetching trending stocks: {e}")
            return {"gainers": [], "losers": []}

    def get_sector_performance(self):
        """
        Get performance by sector using Yahoo Finance data
        """
        try:
            # Use data from trending stocks to avoid additional API calls
            trending_data = self.get_trending_stocks(limit=20)
            all_stocks = trending_data["gainers"] + trending_data["losers"]
            
            # Batch fetch more stocks to cover all sectors
            key_stocks_by_sector = {
                "Banking": ["SBIN", "HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK"],
                "Information Technology": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM"],
                "Oil & Gas": ["RELIANCE", "ONGC", "IOC", "GAIL", "BPCL"],
                "Automobiles": ["MARUTI", "TATAMOTORS", "M&M", "HEROMOTOCO", "BAJAJ-AUTO"],
                "Pharmaceuticals": ["SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "BIOCON"],
                "FMCG": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "DABUR"],
                "Metals": ["TATASTEEL", "HINDALCO", "JSWSTEEL", "COAL", "NMDC"],
                "Power": ["NTPC", "POWERGRID", "TATAPOWER", "ADANIPOWER", "TORNTPOWER"],
                "Telecom": ["BHARTIARTL", "IDEA", "MTNL", "TATACOMM"],
                "Financial Services": ["BAJFINANCE", "HDFCLIFE", "SBILIFE", "ICICIPRULI", "ICICIGI"]
            }
            
            # Collect any missing sectors that need to be fetched
            stocks_to_fetch = []
            exchange = self.default_exchange
            
            # Find sectors we haven't covered in the trending data
            sectors_covered = set()
            for stock in all_stocks:
                if isinstance(stock, dict):
                    sectors_covered.add(stock.get("sector", "Unknown"))
                elif hasattr(stock, "sector"):
                    sectors_covered.add(stock.sector)
            
            # Add stocks for missing sectors
            for sector, stocks in key_stocks_by_sector.items():
                if sector not in sectors_covered:
                    # Add 2 stocks from each missing sector
                    stocks_to_fetch.extend(stocks[:2])
            
            # Fetch additional stocks if needed
            if stocks_to_fetch:
                yf_symbols = [self._format_symbol_for_yf(symbol, exchange) for symbol in stocks_to_fetch]
                
                # Use Yahoo Finance batch API
                data = yf.download(
                    tickers=yf_symbols,
                    period="2d",
                    group_by="ticker",
                    auto_adjust=True,
                    threads=True
                )
                
                # Process each stock
                for i, symbol in enumerate(stocks_to_fetch):
                    yf_symbol = yf_symbols[i]
                    
                    try:
                        # Get stock data from batch request
                        if len(stocks_to_fetch) > 1:
                            stock_data = data[yf_symbol]
                        else:
                            stock_data = data  # For single ticker
                        
                        if stock_data.empty:
                            continue
                        
                        # Calculate day change percentage
                        if len(stock_data) >= 2:
                            today_close = stock_data['Close'].iloc[-1]
                            prev_close = stock_data['Close'].iloc[-2]
                            day_change_pct = ((today_close - prev_close) / prev_close) * 100
                        else:
                            day_change_pct = 0
                        
                        # Add to all_stocks list
                        sector = self.stock_sectors.get(symbol, "Miscellaneous")
                        stock_info = {
                            "symbol": symbol,
                            "exchange": exchange,
                            "name": symbol,  # Simplified
                            "sector": sector,
                            "current_price": stock_data['Close'].iloc[-1],
                            "day_change": day_change_pct
                        }
                        
                        all_stocks.append(stock_info)
                    except Exception as e:
                        logger.warning(f"Error processing sector stock {symbol}: {e}")
                        continue
            
            # Group by sector
            sectors = {}
            for stock in all_stocks:
                sector_name = ""
                day_change = 0
                
                # Handle both dict and object types
                if isinstance(stock, dict):
                    sector_name = stock.get("sector", "Unknown")
                    day_change = stock.get("day_change", 0) or 0
                else:
                    sector_name = getattr(stock, "sector", "Unknown")
                    day_change = getattr(stock, "day_change", 0) or 0
                
                if sector_name not in sectors:
                    sectors[sector_name] = {
                        "name": sector_name,
                        "stocks": [],
                        "avg_change": 0,
                        "count": 0
                    }
                
                sectors[sector_name]["stocks"].append(stock)
                sectors[sector_name]["count"] += 1
                sectors[sector_name]["avg_change"] += day_change
            
            # Calculate average change for each sector
            for sector_name in sectors:
                if sectors[sector_name]["count"] > 0:
                    sectors[sector_name]["avg_change"] /= sectors[sector_name]["count"]
            
            # Convert to list and sort by average change
            sector_list = list(sectors.values())
            sector_list.sort(key=lambda x: x["avg_change"], reverse=True)
            
            return sector_list
        
        except Exception as e:
            logger.error(f"Error calculating sector performance: {e}")
            return []

    def get_stock_news(self, symbol=None, exchange=None, max_results=10):
        """
        Get financial news using Yahoo Finance API
        If symbol is provided, get news for that stock
        Otherwise, get general market news
        """
        try:
            news_items = []
            
            if symbol:
                # Format the symbol for Yahoo Finance
                yf_symbol = self._format_symbol_for_yf(symbol, exchange or self.default_exchange)
                stock = yf.Ticker(yf_symbol)
                
                # Get news for specific stock
                news = stock.news
                if news:
                    for i, item in enumerate(news):
                        if i >= max_results:
                            break
                            
                        # Extract needed information
                        news_item = {
                            "title": item.get("title", ""),
                            "source": item.get("publisher", "Yahoo Finance"),
                            "url": item.get("link", ""),
                            "published_date": datetime.fromtimestamp(item.get("providerPublishTime", 0)),
                            "content": item.get("summary", ""),
                            "summary": item.get("summary", ""),
                            "relevance_score": 1.0,  # Default high relevance for stock-specific news
                            "related_stocks": [symbol]
                        }
                        
                        # Save to database
                        db_service.save_news_item(news_item)
                        news_items.append(news_item)
            else:
                # Get general market news using major indices and popular stocks
                indices = ["^NSEI", "^BSESN"]  # NIFTY 50 and BSE SENSEX
                popular_stocks = ["RELIANCE.NS", "HDFCBANK.NS", "TCS.NS", "INFY.NS"]
                
                for ticker_symbol in indices + popular_stocks:
                    if len(news_items) >= max_results:
                        break
                        
                    try:
                        stock = yf.Ticker(ticker_symbol)
                        news = stock.news
                        
                        if news:
                            # Add unique news items (avoid duplicates)
                            for item in news:
                                # Check if we've reached the limit
                                if len(news_items) >= max_results:
                                    break
                                    
                                # Check if item is already in our results (by title)
                                title = item.get("title", "")
                                if any(n.get("title") == title for n in news_items):
                                    continue
                                
                                # Extract needed information
                                news_item = {
                                    "title": title,
                                    "source": item.get("publisher", "Yahoo Finance"),
                                    "url": item.get("link", ""),
                                    "published_date": datetime.fromtimestamp(item.get("providerPublishTime", 0)),
                                    "content": item.get("summary", ""),
                                    "summary": item.get("summary", ""),
                                    "relevance_score": 0.9,  # Default high relevance
                                    "related_stocks": self._extract_stock_mentions(title + " " + item.get("summary", ""))
                                }
                                
                                # Save to database
                                db_service.save_news_item(news_item)
                                news_items.append(news_item)
                    except Exception as e:
                        logger.warning(f"Error getting news for {ticker_symbol}: {e}")
                        continue
            
            return news_items
        
        except Exception as e:
            logger.error(f"Error fetching stock news: {e}")
            return []
            
    def _extract_stock_mentions(self, text):
        """
        Simple utility to extract potential stock symbols mentioned in the text
        """
        # Get list of known stock symbols
        known_symbols = list(self.stock_sectors.keys())
        
        # Check for each known symbol
        mentioned_stocks = []
        for symbol in known_symbols:
            if symbol in text.upper():
                mentioned_stocks.append(symbol)
                
        return mentioned_stocks
    
    def _format_symbol_for_yf(self, symbol, exchange):
        """
        Format the symbol for Yahoo Finance API
        """
        if exchange == "NSE":
            return f"{symbol}.NS"
        elif exchange == "BSE":
            return f"{symbol}.BO"
        return symbol

# Create instance of the service
stock_service = StockService()
