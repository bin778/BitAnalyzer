import os
from dotenv import load_dotenv
from binance.client import Client

class PriceService:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        
        if not api_key or not api_secret:
            raise ValueError("API 키가 .env 파일에 설정되지 않았습니다.")
            
        self.client = Client(api_key, api_secret)

    def get_btc_usdt_price(self):
        try:
            ticker = self.client.get_ticker(symbol="BTCUSDT")
            return ticker['lastPrice']
        except Exception as e:
            print(f"PriceService API 에러: {e}")
            raise e