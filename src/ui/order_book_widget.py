from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

class OrderBookWidget(BoxLayout):
    def set_loading_state(self):
        self.ids.title_label.text = "Loading..."
        self.ids.bids_layout.clear_widgets()
        self.ids.asks_layout.clear_widgets()
        self.ids.bids_layout.add_widget(Label(text="Loading...", color=(0.8, 0.8, 0.8, 1)))
        self.ids.asks_layout.add_widget(Label(text="Loading...", color=(0.8, 0.8, 0.8, 1)))

    def set_error_state(self):
        self.ids.title_label.text = "ERROR!"
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