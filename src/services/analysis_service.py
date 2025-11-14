def analyze_order_book_trend(bids, asks, strong_threshold=2.0):
    try:
        bid_volume = sum(qty for price, qty in bids)
        ask_volume = sum(qty for price, qty in asks)

        if bid_volume == 0 and ask_volume == 0:
            return {'text': "Trend: No Volume", 'color': (0.8, 0.8, 0.8, 1)}

        if bid_volume > (ask_volume * strong_threshold):
            return {'text': "Trend: Strong Buy Pressure", 'color': (0.4, 1, 0.4, 1)}
        elif ask_volume > (bid_volume * strong_threshold):
            return {'text': "Trend: Strong Sell Pressure", 'color': (1, 0.4, 0.4, 1)}
        else:
            return {'text': "Trend: Balanced", 'color': (0.9, 0.9, 0.9, 1)}
            
    except Exception as e:
        print(f"Trend analysis error: {e}")
        return {'text': "Trend: Analysis Error", 'color': (1, 0.3, 0.3, 1)}

def calculate_k_premium(upbit_data, binance_data, usdt_krw_price):
    try:
        if not usdt_krw_price:
            raise ValueError("Unable to get USDT/KRW exchange rate.")
            
        if 'error' in upbit_data or 'error' in binance_data:
            raise ValueError("Binance OR Upbit Data ERROR!")
            
        if not upbit_data.get('asks') or not upbit_data.get('bids'):
            raise ValueError("Upbit data is incomplete.")
        if not binance_data.get('asks') or not binance_data.get('bids'):
            raise ValueError("Binance data is incomplete.")

        upbit_ask = upbit_data['asks'][0][0]
        upbit_bid = upbit_data['bids'][0][0]
        upbit_mid_price = (upbit_ask + upbit_bid) / 2
        
        binance_ask = binance_data['asks'][0][0]
        binance_bid = binance_data['bids'][0][0]
        binance_mid_price = (binance_ask + binance_bid) / 2
        
        if upbit_mid_price <= 0 or binance_mid_price <= 0:
            raise ValueError("Invalid Price Data")

        binance_price_in_krw = binance_mid_price * usdt_krw_price
        premium_pct = ((upbit_mid_price / binance_price_in_krw) - 1) * 100
        color = (0.4, 1, 0.4, 1) if premium_pct > 0 else (1, 0.4, 0.4, 1)
        
        text = (
            f"K-Premium (Upbit/Binance): {premium_pct:+.2f}% "
            f"(₩{usdt_krw_price:,.0f})"
        )
        return {'text': text, 'color': color}

    except Exception as e:
        print(f"K-Premium Calculation Error: {e}")
        return {'text': f"K-Premium: Error ({e})", 'color': (1, 0.3, 0.3, 1)}