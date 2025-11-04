import os
from dotenv import load_dotenv
from binance.client import Client

load_dotenv()

api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')

client = Client(api_key, api_secret)

try:
    ticker = client.get_ticker(symbol="BTCUSDT")

    print("--- API 연결 성공 ---")
    print(f"BTC/USDT 현재가: {ticker['lastPrice']}")

    # TODO: 계정 정보 (API 키 권한 확인)
except Exception as e:
    print(f"--- API 연결 실패 ---")
    print(f"에러: {e}")