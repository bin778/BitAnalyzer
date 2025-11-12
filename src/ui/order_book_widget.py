from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.clock import Clock
from services.analysis_service import analyze_order_book_trend

class OrderBookWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.ask_labels = []
        self.bid_labels = []

        for _ in range(5):
            self.ask_labels.append({
                'price': Label(text='-', color=(1, 0.4, 0.4, 1), size_hint_x=0.6),
                'qty': Label(text='-', color=(1, 1, 1, 0.7), size_hint_x=0.4, font_size='12sp')
            })
            self.bid_labels.append({
                'price': Label(text='-', color=(0.4, 1, 0.4, 1), size_hint_x=0.6),
                'qty': Label(text='-', color=(1, 1, 1, 0.7), size_hint_x=0.4, font_size='12sp')
            })
        
        Clock.schedule_once(self._populate_layouts)

    def _populate_layouts(self, dt):
        try:
            for i in range(5):
                ask = self.ask_labels[i]
                self.ids.asks_layout.add_widget(ask['price'])
                self.ids.asks_layout.add_widget(ask['qty'])
                
                bid = self.bid_labels[i]
                self.ids.bids_layout.add_widget(bid['price'])
                self.ids.bids_layout.add_widget(bid['qty'])
        except Exception as e:
            print(f"Error populating layouts: {e}. Retrying...")
            Clock.schedule_once(self._populate_layouts, 0.1)

    def _set_ob_labels(self, text, qty_text=""):
        if not self.ask_labels:
            return
            
        qty_text = qty_text or text
        for i in range(5):
            self.ask_labels[i]['price'].text = text
            self.ask_labels[i]['qty'].text = qty_text
            self.bid_labels[i]['price'].text = text
            self.bid_labels[i]['qty'].text = qty_text

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
        if not self.ask_labels or not self.ids.asks_layout.children:
            self.set_loading_state()
            return

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
                self.ask_labels[i]['price'].text = price_str
                self.ask_labels[i]['qty'].text = qty_str
            else:
                self.ask_labels[i]['price'].text = '-'
                self.ask_labels[i]['qty'].text = '-'

        for i in range(5):
            if i < len(bids):
                price, qty = bids[i]
                price_str = f"₩{price:,.0f}" if is_krw else f"${price:,.2f}"
                qty_str = f"{qty:.4f}"
                self.bid_labels[i]['price'].text = price_str
                self.bid_labels[i]['qty'].text = qty_str
            else:
                self.bid_labels[i]['price'].text = '-'
                self.bid_labels[i]['qty'].text = '-'