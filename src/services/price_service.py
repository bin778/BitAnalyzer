import os, ccxt
from dotenv import load_dotenv

class PriceService:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        
        if not api_key or not api_secret:
            raise ValueError("API key is not set in .env file.")
            
        self.binance_client = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'options': {'defaultType': 'spot'}
        })
        
        self.upbit_client = ccxt.upbit()
        self.bybit_client = ccxt.bybit()

    def get_btc_order_book(self, client_name, symbol, limit=5):
        try:
            client = getattr(self, f"{client_name.lower()}_client")
            ob = client.fetch_l2_order_book(symbol, limit=limit)
            return {
                'symbol': symbol, 
                'bids': ob['bids'],
                'asks': ob['asks']
            }
        except Exception as e:
            print(f"{client_name} OrderBook API Error: {e}")
            return {'error': str(e)}
    
    def get_ticker(self, client_name, symbol):
        try:
            client = getattr(self, f"{client_name.lower()}_client")
            ticker = client.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'last': ticker.get('last'),
                'change_pct': ticker.get('percentage') 
            }
        except Exception as e:
            print(f"{client_name} Ticker API Error: {e}")
            return {'error': str(e)}

    def get_usdt_krw_price(self):
        try:
            ticker = self.upbit_client.fetch_ticker('USDT/KRW')
            return ticker['last']
        except Exception as e:
            print(f"Upbit USDT/KRW Ticker API Error: {e}")
            return None
    
    def get_all_markets(self, exchange_name):
        try:
            client = getattr(self, f"{exchange_name.lower()}_client")
            
            markets = client.load_markets()
            
            market_list = []
            for symbol, info in markets.items():
                market_list.append({
                    'symbol': symbol,
                    'base': info.get('base'),
                    'quote': info.get('quote'),
                    'active': info.get('active', True)
                })
            return market_list
            
        except Exception as e:
            print(f"{exchange_name} Market Load Error: {e}")
            return []