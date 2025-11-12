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
            'options': {'defaultType': 'spot'}
        })
        
        self.upbit_client = ccxt.upbit()
        self.bybit_client = ccxt.bybit()

    def get_btc_order_book(self, client_name, symbol, limit=5):
        """ 지정된 클라이언트의 호가창 정보를 가져옵니다. (병렬 호출용) """
        try:
            client = getattr(self, f"{client_name.lower()}_client")
            ob = client.fetch_l2_order_book(symbol, limit=limit)
            return {
                'symbol': symbol, 
                'bids': ob['bids'],
                'asks': ob['asks']
            }
        except Exception as e:
            print(f"{client_name} OrderBook API 에러: {e}")
            return {'error': str(e)}

    def get_usdt_krw_price(self):
        """ 업비트 USDT/KRW 환율을 가져옵니다. (병렬 호출용) """
        try:
            ticker = self.upbit_client.fetch_ticker('USDT/KRW')
            return ticker['last']
        except Exception as e:
            print(f"Upbit USDT/KRW Ticker API 에러: {e}")
            return None