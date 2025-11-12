from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from services.analysis_service import analyze_order_book_trend

class OrderBookWidget(BoxLayout):
    def _set_ob_labels(self, text, qty_text=""):
        for i in range(5):
            self.ids[f'ask_price_{i}'].text = text
            self.ids[f'ask_qty_{i}'].text = qty_text
            self.ids[f'bid_price_{i}'].text = text
            self.ids[f'bid_qty_{i}'].text = qty_text

    def set_loading_state(self):
        self.ids.title_label.text = "Loading..."
        self.ids.trend_label.text = "Trend: Calculating..."
        self.ids.trend_label.color = (0.8, 0.8, 0.8, 1)
        self._set_ob_labels("Loading...")

    def set_error_state(self):
        self.ids.title_label.text = "ERROR"
        self.ids.trend_label.text = "Trend: Error"
        self.ids.trend_label.color = (1, 0.3, 0.3, 1)
        self._set_ob_labels("Error", "Error")

    def update_data(self, exchange_name, data):
        
        if not data or 'error' in data:
            self.set_error_state()
            if data and 'error' in data:
                print(f"{exchange_name} Error: {data['error']}")
            return
        
        symbol = data.get('symbol', 'N/A')
        bids = data.get('bids', [])
        asks = data.get('asks', [])
        
        self.ids.title_label.text = f"{exchange_name} ({symbol})"
        
        trend_result = analyze_order_book_trend(bids, asks)
        self.ids.trend_label.text = trend_result['text']
        self.ids.trend_label.color = trend_result['color']

        is_krw = 'KRW' in symbol

        for i in range(5):
            if i < len(asks):
                price, qty = asks[-(i+1)] 
                price_str = f"₩{price:,.0f}" if is_krw else f"${price:,.2f}"
                qty_str = f"{qty:.4f}"
                self.ids[f'ask_price_{i}'].text = price_str
                self.ids[f'ask_qty_{i}'].text = qty_str
            else:
                self.ids[f'ask_price_{i}'].text = '-'
                self.ids[f'ask_qty_{i}'].text = '-'

        for i in range(5):
            if i < len(bids):
                price, qty = bids[i]
                price_str = f"₩{price:,.0f}" if is_krw else f"${price:,.2f}"
                qty_str = f"{qty:.4f}"
                self.ids[f'bid_price_{i}'].text = price_str
                self.ids[f'bid_qty_{i}'].text = qty_str
            else:
                self.ids[f'bid_price_{i}'].text = '-'
                self.ids[f'bid_qty_{i}'].text = '-'