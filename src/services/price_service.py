import os, ccxt
from dotenv import load_dotenv

class PriceService:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        
        if not api_key or not api_secret:
            raise ValueError("API 키가 .env 파일에 설정되지 않았습니다.")
            
        self.binance_client = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
        })
        
        self.upbit_client = ccxt.upbit()
        self.bybit_client = ccxt.bybit()

    def get_all_btc_prices(self):
        prices = {}

        try:
            ticker = self.binance_client.fetch_ticker('BTC/USDT')
            prices['binance'] = {'symbol': 'BTC/USDT', 'price': ticker['last']}
        except Exception as e:
            print(f"Binance API 에러: {e}")
            prices['binance'] = {'error': str(e)}
        try:
            ticker = self.upbit_client.fetch_ticker('BTC/KRW')
            prices['upbit'] = {'symbol': 'BTC/KRW', 'price': ticker['last']}
        except Exception as e:
            print(f"Upbit API 에러: {e}")
            prices['upbit'] = {'error': str(e)}
        try:
            ticker = self.bybit_client.fetch_ticker('BTC/USDT')
            prices['bybit'] = {'symbol': 'BTC/USDT', 'price': ticker['last']}
        except Exception as e:
            print(f"Bybit API 에러: {e}")
            prices['bybit'] = {'error': str(e)}
            
        return prices
    
    def get_all_btc_order_books(self, limit=5):
        order_books = {}

        try:
            ob = self.binance_client.fetch_l2_order_book('BTC/USDT', limit=limit)
            order_books['binance'] = {
                'symbol': 'BTC/USDT', 
                'bids': ob['bids'],
                'asks': ob['asks']
            }
        except Exception as e:
            print(f"Binance OrderBook API 에러: {e}")
            order_books['binance'] = {'error': str(e)}

        try:
            ob = self.upbit_client.fetch_l2_order_book('BTC/KRW', limit=limit)
            order_books['upbit'] = {
                'symbol': 'BTC/KRW',
                'bids': ob['bids'],
                'asks': ob['asks']
            }
        except Exception as e:
            print(f"Upbit OrderBook API 에러: {e}")
            order_books['upbit'] = {'error': str(e)}

        try:
            ob = self.bybit_client.fetch_l2_order_book('BTC/USDT', limit=limit)
            order_books['bybit'] = {
                'symbol': 'BTC/USDT',
                'bids': ob['bids'],
                'asks': ob['asks']
            }
        except Exception as e:
            print(f"Bybit OrderBook API 에러: {e}")
            order_books['bybit'] = {'error': str(e)}
            
        return order_books
    
    def get_usdt_krw_price(self):
        try:
            ticker = self.upbit_client.fetch_ticker('USDT/KRW')
            return ticker['last']
        except Exception as e:
            print(f"Upbit USDT/KRW Ticker API 에러: {e}")
            return None