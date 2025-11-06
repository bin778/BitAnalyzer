import threading
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

class PriceTrackerLayout(BoxLayout):
    def __init__(self, price_service, **kwargs):
        super().__init__(**kwargs)
        self.price_service = price_service
        Clock.schedule_once(self.start_fetch_thread, 0)

    def start_fetch_thread(self, instance=None):
        self.ids.binance_label.text = 'Binance: Loading...'
        self.ids.upbit_label.text = 'Upbit: Loading...'
        self.ids.bybit_label.text = 'Bybit: Loading...'
        
        threading.Thread(target=self.fetch_price_data, daemon=True).start()

    def fetch_price_data(self):
        try:
            all_prices = self.price_service.get_all_btc_prices()
            Clock.schedule_once(lambda dt: self.update_ui(all_prices))
        except Exception as e:
            print(f"전체 fetch 에러: {e}")
            Clock.schedule_once(lambda dt: self.update_ui_error())

    def update_ui(self, all_prices):
        bin_data = all_prices.get('binance')
        if bin_data and 'price' in bin_data:
            price = bin_data['price']
            self.ids.binance_label.text = f"Binance (BTC/USDT): ${price:,.2f}"
        else:
            self.ids.binance_label.text = "Binance: ERROR"

        upbit_data = all_prices.get('upbit')
        if upbit_data and 'price' in upbit_data:
            price = upbit_data['price']
            self.ids.upbit_label.text = f"Upbit (BTC/KRW): ₩{price:,.0f}"
        else:
            self.ids.upbit_label.text = "Upbit: ERROR"

        bybit_data = all_prices.get('bybit')
        if bybit_data and 'price' in bybit_data:
            price = bybit_data['price']
            self.ids.bybit_label.text = f"Bybit (BTC/USDT): ${price:,.2f}"
        else:
            self.ids.bybit_label.text = "Bybit: ERROR"

    def update_ui_error(self):
        self.ids.binance_label.text = "Binance: ERROR!"
        self.ids.upbit_label.text = "Upbit: ERROR!"
        self.ids.bybit_label.text = "Bybit: ERROR!"