import yfinance as yf
import pandas as pd
import logging
from datetime import datetime, timedelta
import json
from config import DEFAULT_STOCKS, INDIAN_MARKET_INDICES

logger = logging.getLogger(__name__)

class YahooFinanceAPI:
    def __init__(self):
        self.default_stocks = DEFAULT_STOCKS
        self.market_indices = INDIAN_MARKET_INDICES
    
    def get_stock_data(self, symbol, period="1mo", interval="1d"):
        """
        Get historical stock data for a specific symbol
        
        Args:
            symbol (str): Stock symbol (e.g., RELIANCE.NS for NSE)
            period (str): Period for historical data (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval (str): Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            
        Returns:
            dict: Stock data including price history and basic info
        """
        try:
            # Add .NS suffix if not already present for NSE stocks
            if '.NS' not in symbol and '.BO' not in symbol:
                # Check if it's likely an Indian stock
                if any(char.isalpha() for char in symbol):
                    symbol = f"{symbol}.NS"
            
            stock = yf.Ticker(symbol)
            
            # Get historical data
            hist = stock.history(period=period, interval=interval)
            
            # Get stock info
            info = stock.info
            
            # Process historical data
            if not hist.empty:
                hist_dict = hist.reset_index().to_dict(orient='records')
                
                # Convert datetime to string for JSON serialization
                for record in hist_dict:
                    if 'Date' in record and isinstance(record['Date'], pd.Timestamp):
                        record['Date'] = record['Date'].strftime('%Y-%m-%d %H:%M:%S')
                    if 'Datetime' in record and isinstance(record['Datetime'], pd.Timestamp):
                        record['Datetime'] = record['Datetime'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                hist_dict = []
            
            # Extract key metrics
            key_metrics = {
                'symbol': symbol,
                'shortName': info.get('shortName', ''),
                'longName': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'marketCap': info.get('marketCap', None),
                'currentPrice': info.get('currentPrice', info.get('regularMarketPrice', None)),
                'previousClose': info.get('previousClose', None),
                'open': info.get('open', None),
                'dayHigh': info.get('dayHigh', None),
                'dayLow': info.get('dayLow', None),
                'volume': info.get('volume', None),
                'averageVolume': info.get('averageVolume', None),
                'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh', None),
                'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow', None),
                'peRatio': info.get('trailingPE', None),
                'eps': info.get('trailingEps', None),
                'dividendYield': info.get('dividendYield', None) * 100 if info.get('dividendYield') else None,
                'beta': info.get('beta', None),
                'forwardPE': info.get('forwardPE', None),
                'bookValue': info.get('bookValue', None),
                'priceToBook': info.get('priceToBook', None),
                'currency': info.get('currency', 'INR'),
                'exchange': info.get('exchange', 'NSE'),
            }
            
            return {
                'info': key_metrics,
                'history': hist_dict,
                'timestamp': datetime.now().isoformat(),
                'period': period,
                'interval': interval
            }
            
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            return {
                'error': str(e),
                'symbol': symbol,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_multiple_stocks(self, symbols=None, period="1d", interval="1d"):
        """
        Get data for multiple stocks
        
        Args:
            symbols (list): List of stock symbols (if None, default_stocks will be used)
            period (str): Period for historical data
            interval (str): Data interval
            
        Returns:
            dict: Data for multiple stocks
        """
        if symbols is None:
            symbols = [stock['symbol'] for stock in self.default_stocks]
        
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_stock_data(symbol, period, interval)
        
        return {
            'stocks': results,
            'timestamp': datetime.now().isoformat(),
            'count': len(results)
        }
    
    def get_market_summary(self, indices=None):
        """
        Get summary data for major Indian market indices
        
        Args:
            indices (list): List of indices to include
            
        Returns:
            dict: Market summary data
        """
        if indices is None:
            indices = ["^NSEI", "^BSESN"]  # NSE Nifty 50 and BSE Sensex
        
        results = {}
        for index in indices:
            try:
                ticker = yf.Ticker(index)
                info = ticker.info
                hist = ticker.history(period="5d")
                
                if not hist.empty:
                    change = hist['Close'].iloc[-1] - hist['Close'].iloc[-2]
                    change_percent = (change / hist['Close'].iloc[-2]) * 100
                else:
                    change = None
                    change_percent = None
                
                results[index] = {
                    'name': info.get('shortName', ''),
                    'last': info.get('regularMarketPrice', None),
                    'change': change,
                    'changePercent': change_percent,
                    'previousClose': info.get('regularMarketPreviousClose', None),
                    'open': info.get('regularMarketOpen', None),
                    'dayHigh': info.get('regularMarketDayHigh', None),
                    'dayLow': info.get('regularMarketDayLow', None)
                }
            except Exception as e:
                logger.error(f"Error fetching data for index {index}: {e}")
                results[index] = {'error': str(e)}
        
        return {
            'indices': results,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_sector_performance(self, sectors=None):
        """
        Get performance data for Indian market sectors
        
        Args:
            sectors (list): List of sector ETFs/indices to track
            
        Returns:
            dict: Sector performance data
        """
        # If no sectors provided, use these sector proxies
        if sectors is None:
            # Using Nifty sector indices
            sectors = [
                "NIFTY BANK.NS",    # Banking
                "NIFTY IT.NS",      # Information Technology
                "NIFTY PHARMA.NS",  # Pharmaceutical
                "NIFTY AUTO.NS",    # Automobile
                "NIFTY FMCG.NS",    # Fast Moving Consumer Goods
                "NIFTY METAL.NS",   # Metal
                "NIFTY REALTY.NS",  # Real Estate
                "NIFTY ENERGY.NS",  # Energy
            ]
        
        results = {}
        for sector in sectors:
            try:
                data = self.get_stock_data(sector, period="1mo")
                
                if 'info' in data:
                    results[sector] = {
                        'name': data['info'].get('shortName', sector),
                        'currentValue': data['info'].get('currentPrice', None),
                        'change': data['info'].get('currentPrice', 0) - data['info'].get('previousClose', 0) 
                            if data['info'].get('currentPrice') and data['info'].get('previousClose') else None,
                        'changePercent': ((data['info'].get('currentPrice', 0) - data['info'].get('previousClose', 0)) / 
                                         data['info'].get('previousClose', 1)) * 100 
                            if data['info'].get('currentPrice') and data['info'].get('previousClose') else None,
                        'weekChange': None,  # Would need to calculate from history
                        'monthChange': None  # Would need to calculate from history
                    }
                    
                    # Calculate week and month changes if history available
                    if 'history' in data and data['history']:
                        history = data['history']
                        if len(history) >= 5:  # At least 5 days for week change
                            week_start = history[0]['Close'] if 'Close' in history[0] else None
                            week_end = history[-1]['Close'] if 'Close' in history[-1] else None
                            if week_start and week_end:
                                results[sector]['weekChange'] = ((week_end - week_start) / week_start) * 100
                        
                        if len(history) >= 20:  # At least 20 days for month change
                            month_start = history[0]['Close'] if 'Close' in history[0] else None
                            month_end = history[-1]['Close'] if 'Close' in history[-1] else None
                            if month_start and month_end:
                                results[sector]['monthChange'] = ((month_end - month_start) / month_start) * 100
            except Exception as e:
                logger.error(f"Error fetching data for sector {sector}: {e}")
                results[sector] = {'error': str(e)}
        
        return {
            'sectors': results,
            'timestamp': datetime.now().isoformat()
        }
    
    def search_stocks(self, query, limit=10, exchanges=None):
        """
        Search for stocks based on name or symbol
        
        Args:
            query (str): Search query
            limit (int): Maximum number of results
            exchanges (list): List of exchanges to include (default: NSE, BSE)
            
        Returns:
            dict: Search results
        """
        if exchanges is None:
            exchanges = ["NSE", "BSE"]
        
        try:
            # Using yfinance's search functionality is limited, so we'll implement a basic search
            results = []
            
            # Search in default stocks first
            for stock in self.default_stocks:
                if (query.lower() in stock['symbol'].lower() or 
                    query.lower() in stock['name'].lower()):
                    
                    # Get basic info about the stock
                    stock_data = self.get_stock_data(stock['symbol'])
                    if 'error' not in stock_data:
                        results.append(stock_data['info'])
            
            # Also search in market indices
            for index in self.market_indices:
                if (query.lower() in index['symbol'].lower() or 
                    query.lower() in index['name'].lower()):
                    
                    # Get basic info about the index
                    index_data = self.get_stock_data(index['symbol'])
                    if 'error' not in index_data:
                        # Add additional market index info
                        index_data['info']['description'] = index.get('description', '')
                        index_data['info']['category'] = index.get('category', '')
                        index_data['info']['is_index'] = True
                        results.append(index_data['info'])
            
            # If we don't have enough results, we could expand the search
            # This would require a more comprehensive list of Indian stocks
            
            return {
                'query': query,
                'results': results[:limit],
                'count': len(results[:limit]),
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error searching for stocks with query {query}: {e}")
            return {
                'error': str(e),
                'query': query,
                'results': [],
                'timestamp': datetime.now().isoformat()
            }
            
    def get_all_market_indices(self, period="1mo", interval="1d", category=None):
        """
        Get data for all configured Indian market indices
        
        Args:
            period (str): Period for historical data
            interval (str): Data interval
            category (str): Optional filter by category (Broad Market, Sector, Market Cap, Strategy)
            
        Returns:
            dict: Data for all market indices
        """
        results = {}
        
        # Filter indices by category if provided
        indices_to_fetch = self.market_indices
        if category:
            indices_to_fetch = [idx for idx in self.market_indices if idx.get('category') == category]
        
        for index in indices_to_fetch:
            symbol = index['symbol']
            try:
                data = self.get_stock_data(symbol, period, interval)
                
                if 'info' in data:
                    # Add additional index information
                    data['info']['description'] = index.get('description', '')
                    data['info']['category'] = index.get('category', '')
                    data['info']['is_index'] = True
                    results[symbol] = data
                    
            except Exception as e:
                logger.error(f"Error fetching data for index {symbol}: {e}")
                results[symbol] = {'error': str(e), 'symbol': symbol}
        
        return {
            'indices': results,
            'timestamp': datetime.now().isoformat(),
            'count': len(results)
        }
    
    def get_indices_by_category(self):
        """
        Get all market indices organized by category
        
        Returns:
            dict: Indices organized by category
        """
        categories = {}
        
        for index in self.market_indices:
            category = index.get('category', 'Other')
            
            if category not in categories:
                categories[category] = []
                
            # Get basic index data
            try:
                ticker = yf.Ticker(index['symbol'])
                info = ticker.info
                hist = ticker.history(period="5d")
                
                if not hist.empty:
                    change = hist['Close'].iloc[-1] - hist['Close'].iloc[-2]
                    change_percent = (change / hist['Close'].iloc[-2]) * 100
                else:
                    change = None
                    change_percent = None
                
                index_data = {
                    'symbol': index['symbol'],
                    'name': index['name'],
                    'description': index.get('description', ''),
                    'last': info.get('regularMarketPrice', None),
                    'change': change,
                    'changePercent': change_percent,
                    'previousClose': info.get('regularMarketPreviousClose', None),
                }
                
                categories[category].append(index_data)
                
            except Exception as e:
                logger.error(f"Error fetching basic data for index {index['symbol']}: {e}")
                categories[category].append({
                    'symbol': index['symbol'],
                    'name': index['name'],
                    'description': index.get('description', ''),
                    'error': str(e)
                })
        
        return {
            'categories': categories,
            'timestamp': datetime.now().isoformat()
        }
