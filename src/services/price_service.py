import os, asyncio
import ccxt.async_support as ccxt
from dotenv import load_dotenv
from datetime import datetime

class PriceService:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        
        self.binance_client = ccxt.binance({'apiKey': api_key, 'secret': api_secret})
        self.upbit_client = ccxt.upbit()
        self.bybit_client = ccxt.bybit()
        self.bitfinex_client = ccxt.bitfinex()
        self.kucoin_client = ccxt.kucoin()
        
        self.clients = [
            self.binance_client, self.upbit_client, self.bybit_client,
            self.bitfinex_client, self.kucoin_client
        ]

    async def close_all(self):
        for client in self.clients:
            await client.close()
    
    async def get_usdt_krw_price(self):
        try:
            ticker = await self.upbit_client.fetch_ticker('USDT/KRW')
            return ticker['last']
        except Exception as e:
            print(f"USDT/KRW Error: {e}")
            return None

    async def get_btc_order_book(self, client_name, symbol, limit=5):
        try:
            client = getattr(self, f"{client_name.lower()}_client")
            
            request_limit = limit
            if client_name.lower() == 'bitfinex':
                request_limit = 25
            elif client_name.lower() == 'kucoin':
                request_limit = 20
            
            ob = await client.fetch_l2_order_book(symbol, limit=request_limit)
            
            return {
                'symbol': symbol, 
                'bids': ob['bids'][:limit], 
                'asks': ob['asks'][:limit]
            }
        except Exception as e:
            print(f"{client_name} OrderBook Error: {e}")
            return {'error': str(e)}
    
    async def get_ticker(self, client_name, symbol):
        try:
            client = getattr(self, f"{client_name.lower()}_client")
            ticker = await client.fetch_ticker(symbol)
            return {'symbol': symbol, 'last': ticker.get('last'), 'change_pct': ticker.get('percentage')}
        except Exception as e:
            print(f"{client_name} Ticker Error: {e}")
            return {'error': str(e)}
    
    async def get_all_markets(self, exchange_name):
        try:
            client = getattr(self, f"{exchange_name.lower()}_client")
            markets = await client.load_markets()
            
            return [{
                'symbol': s, 
                'base': i['base'], 
                'quote': i['quote'], 
                'active': i.get('active', True)
            } for s, i in markets.items()]
        except Exception as e:
            print(f"Market Load Error ({exchange_name}): {e}")
            return []

    async def fetch_all_tickers(self, targets):
        """
        targets: [{'exchange': 'Binance', 'symbol': 'BTC/USDT'}, ...]
        """
        tasks = [self.get_ticker(t['exchange'], t['symbol']) for t in targets]
        return await asyncio.gather(*tasks)

    async def fetch_ohlcv_history(self, exchange_name, symbol, period):
        try:
            client = getattr(self, f"{exchange_name.lower()}_client")
            timeframe = '1h'
            limit = 100
            
            if period == '1D':
                timeframe = '15m'
                limit = 96
            elif period == '1M':
                timeframe = '4h'
                limit = 180
            elif period == '3M':
                timeframe = '1d'
                limit = 90
            elif period == '1Y':
                timeframe = '1d'
                limit = 365

            if client.has['fetchOHLCV']:
                ohlcv = await client.fetch_ohlcv(symbol, timeframe, limit=limit)
                
                history = []
                for candle in ohlcv:
                    history.append({
                        'ts': datetime.fromtimestamp(candle[0]/1000),
                        'price': candle[4],
                        'bid': candle[3],
                        'high': candle[2],
                        'low': candle[3]
                    })
                return history
            else:
                print(f"{exchange_name} does not support OHLCV.")
                return []
                
        except Exception as e:
            print(f"OHLCV Error: {e}")
            return []