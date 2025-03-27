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
        Get trending stocks (top gainers and losers)
        """
        try:
            # Either use the database for trending stocks or fetch directly
            trending = db_service.get_trending_stocks(limit=limit)
            
            # If database couldn't provide trending stocks, fall back to a default list
            if not trending["gainers"] and not trending["losers"]:
                popular_stocks = [
                    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
                    "HINDUNILVR", "SBIN", "BAJFINANCE", "ITC", "KOTAKBANK"
                ]
                
                exchange = exchange or self.default_exchange
                gainers = []
                losers = []
                
                for symbol in popular_stocks:
                    stock_data = self.get_stock_data(symbol, exchange)
                    if stock_data:
                        if stock_data.get("day_change", 0) > 0:
                            gainers.append(stock_data)
                        else:
                            losers.append(stock_data)
                
                # Sort by day_change
                gainers.sort(key=lambda x: x.get("day_change", 0), reverse=True)
                losers.sort(key=lambda x: x.get("day_change", 0))
                
                # Limit to requested size
                trending = {
                    "gainers": gainers[:limit//2],
                    "losers": losers[:limit//2]
                }
            
            return trending
        
        except Exception as e:
            logger.error(f"Error fetching trending stocks: {e}")
            return {"gainers": [], "losers": []}

    def get_sector_performance(self):
        """
        Get performance by sector
        """
        try:
            # Get stocks grouped by sector
            sectors = {}
            
            for symbol in self.stock_sectors.keys():
                stock_data = self.get_stock_data(symbol)
                if stock_data:
                    sector = stock_data["sector"]
                    if sector not in sectors:
                        sectors[sector] = {
                            "stocks": [],
                            "avg_change": 0,
                            "count": 0
                        }
                    
                    sectors[sector]["stocks"].append(stock_data)
                    sectors[sector]["count"] += 1
                    sectors[sector]["avg_change"] += stock_data.get("day_change", 0) or 0
            
            # Calculate average change for each sector
            for sector in sectors:
                if sectors[sector]["count"] > 0:
                    sectors[sector]["avg_change"] /= sectors[sector]["count"]
            
            # Sort sectors by average change
            sorted_sectors = sorted(
                sectors.items(), 
                key=lambda x: x[1]["avg_change"], 
                reverse=True
            )
            
            return sorted_sectors
        
        except Exception as e:
            logger.error(f"Error calculating sector performance: {e}")
            return []

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
