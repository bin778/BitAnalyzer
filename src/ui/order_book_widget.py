from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

class OrderBookWidget(BoxLayout):
    def set_loading_state(self):
        self.ids.title_label.text = "Loading..."
        self.ids.trend_label.text = "Trend: Calculating..."
        self.ids.trend_label.color = (0.8, 0.8, 0.8, 1)
        self.ids.bids_layout.clear_widgets()
        self.ids.asks_layout.clear_widgets()
        self.ids.bids_layout.add_widget(Label(text="Loading...", color=(0.8, 0.8, 0.8, 1)))
        self.ids.asks_layout.add_widget(Label(text="Loading...", color=(0.8, 0.8, 0.8, 1)))

    def set_error_state(self):
        self.ids.title_label.text = "ERROR"
        self.ids.trend_label.text = "Trend: Error"
        self.ids.trend_label.color = (1, 0.3, 0.3, 1)
        self.ids.bids_layout.clear_widgets()
        self.ids.asks_layout.clear_widgets()
        self.ids.bids_layout.add_widget(Label(text="Error", color=(1, 0.3, 0.3, 1)))
        self.ids.asks_layout.add_widget(Label(text="Error", color=(1, 0.3, 0.3, 1)))

    def update_data(self, exchange_name, data):
        self.ids.bids_layout.clear_widgets()
        self.ids.asks_layout.clear_widgets()

        if not data or 'error' in data:
            self.set_error_state()
            if data and 'error' in data:
                print(f"{exchange_name} Error: {data['error']}")
            return
        
        symbol = data.get('symbol', 'N/A')
        bids = data.get('bids', [])
        asks = data.get('asks', [])
        
        self.ids.title_label.text = f"{exchange_name} ({symbol})"
        self.analyze_trend(bids, asks)

        for ask in reversed(asks):
            price, qty = ask
            is_krw = 'KRW' in symbol
            price_str = f"₩{price:,.0f}" if is_krw else f"${price:,.2f}"
            qty_str = f"{qty:.4f}"
            
            self.ids.asks_layout.add_widget(
                Label(text=f"{price_str}", color=(1, 0.4, 0.4, 1), size_hint_x=0.6)
            )
            self.ids.asks_layout.add_widget(
                Label(text=f"{qty_str}", color=(1, 1, 1, 0.7), size_hint_x=0.4, font_size='12sp')
            )

        for bid in bids:
            price, qty = bid
            is_krw = 'KRW' in symbol
            price_str = f"₩{price:,.0f}" if is_krw else f"${price:,.2f}"
            qty_str = f"{qty:.4f}"
            
            self.ids.bids_layout.add_widget(
                Label(text=f"{price_str}", color=(0.4, 1, 0.4, 1), size_hint_x=0.6)
            )
            self.ids.bids_layout.add_widget(
                Label(text=f"{qty_str}", color=(1, 1, 1, 0.7), size_hint_x=0.4, font_size='12sp')
            )

    def analyze_trend(self, bids, asks):
        try:
            bid_volume = sum(qty for price, qty in bids)
            ask_volume = sum(qty for price, qty in asks)
    
            if bid_volume == 0 and ask_volume == 0:
                self.ids.trend_label.text = "Trend: No Volume"
                self.ids.trend_label.color = (0.8, 0.8, 0.8, 1)
                return
    
            strong_threshold = 2.0 
    
            if bid_volume > (ask_volume * strong_threshold):
                self.ids.trend_label.text = "Trend: Strong Buy Pressure"
                self.ids.trend_label.color = (0.4, 1, 0.4, 1)
            elif ask_volume > (bid_volume * strong_threshold):
                self.ids.trend_label.text = "Trend: Strong Sell Pressure"
                self.ids.trend_label.color = (1, 0.4, 0.4, 1)
            else:
                self.ids.trend_label.text = "Trend: Balanced"
                self.ids.trend_label.color = (0.9, 0.9, 0.9, 1)
                
        except Exception as e:
            print(f"Trend analysis error: {e}")
            self.ids.trend_label.text = "Trend: Analysis Error"
            self.ids.trend_label.color = (1, 0.3, 0.3, 1)