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