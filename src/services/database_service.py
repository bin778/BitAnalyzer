import os, urllib.parse
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

try:
    from pymongo import MongoClient, ASCENDING, DESCENDING
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False
    print("Warning: 'pymongo' not installed. Database features disabled.")

class DatabaseService:
    def __init__(self):
        self.enabled = MONGO_AVAILABLE
        if not self.enabled:
            return

        load_dotenv()
        
        host = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        db_name = os.getenv("MONGO_DB_NAME", "bitanalyzer_db")
        user = os.getenv("MONGO_USER")
        password = os.getenv("MONGO_PASSWORD")

        try:
            if user and password:
                username = urllib.parse.quote_plus(user)
                pwd = urllib.parse.quote_plus(password)
                
                if "mongodb://" in host:
                    connection_string = host.replace("mongodb://", f"mongodb://{username}:{pwd}@")
                else:
                    connection_string = f"mongodb://{username}:{pwd}@{host}"
            else:
                connection_string = host

            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=2000)
            self.db = self.client[db_name]
            self.collection = self.db["market_tickers"]
            
            try:
                self.collection.create_index("timestamp", expireAfterSeconds=31536000)
            except:
                pass
                
            self.collection.create_index([("symbol", ASCENDING), ("exchange", ASCENDING), ("timestamp", DESCENDING)])
            print("✅ MongoDB Connected Successfully.")
            
        except Exception as e:
            print(f"❌ MongoDB Connection Error: {e}")
            self.enabled = False

    def save_ticker(self, exchange, symbol, price, best_bid, best_ask):
        if not self.enabled: return

        data = {
            "exchange": exchange,
            "symbol": symbol,
            "price": float(price),
            "best_bid": float(best_bid) if best_bid else 0,
            "best_ask": float(best_ask) if best_ask else 0,
            "timestamp": datetime.now(timezone.utc)
        }
        
        try:
            self.collection.insert_one(data)
        except Exception as e:
            print(f"DB Save Error: {e}")

    def get_price_history(self, exchange, symbol, period_code):
        if not self.enabled: return []

        now = datetime.now(timezone.utc)
        start_time = now

        if period_code == '1D':
            start_time = now - timedelta(days=1)
        elif period_code == '1M':
            start_time = now - timedelta(days=30)
        elif period_code == '3M':
            start_time = now - timedelta(days=90)
        elif period_code == '1Y':
            start_time = now - timedelta(days=365)

        query = {
            "exchange": exchange,
            "symbol": symbol,
            "timestamp": {"$gte": start_time}
        }

        cursor = self.collection.find(query).sort("timestamp", ASCENDING).limit(1000)
        
        history = []
        for doc in cursor:
            history.append({
                'ts': doc['timestamp'],
                'price': doc['price'],
                'bid': doc.get('best_bid', 0),
                'ask': doc.get('best_ask', 0)
            })
            
        return history