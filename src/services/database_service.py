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
        db_name = os.getenv("MONGO_DB_NAME") 
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
            
            self.spread_col = self.db["spread_history"]
            
            try:
                self.spread_col.create_index("timestamp", expireAfterSeconds=604800)
            except:
                pass
            
            self.spread_col.create_index([("exchange", ASCENDING), ("symbol", ASCENDING), ("timestamp", DESCENDING)])
            
            print(f"✅ MongoDB Connected to '{db_name}'. Collection: 'spread_history'")
            
        except Exception as e:
            print(f"❌ MongoDB Connection Error: {e}")
            self.enabled = False

    def save_spread(self, exchange, symbol, best_bid, best_ask):
        if not self.enabled: return

        if best_bid <= 0 or best_ask <= 0:
            return

        data = {
            "exchange": exchange,
            "symbol": symbol,
            "bid": float(best_bid),
            "ask": float(best_ask),
            "spread": float(best_ask - best_bid),
            "timestamp": datetime.now(timezone.utc)
        }
        
        try:
            self.spread_col.insert_one(data)
        except Exception as e:
            print(f"DB Save Error: {e}")

    def get_spread_history(self, exchange, symbol, period_code):
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
        else:
            start_time = now - timedelta(hours=24)

        query = {
            "exchange": exchange,
            "symbol": symbol,
            "timestamp": {"$gte": start_time}
        }

        cursor = self.spread_col.find(query).sort("timestamp", ASCENDING).limit(3000)
        
        history = []
        for doc in cursor:
            history.append({
                'ts': doc['timestamp'],
                'bid': doc.get('bid', 0),
                'ask': doc.get('ask', 0),
                'spread': doc.get('spread', 0)
            })
            
        return history