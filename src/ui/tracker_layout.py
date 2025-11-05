import threading
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

class PriceTrackerLayout(BoxLayout):
    def __init__(self, price_service, **kwargs):
        super().__init__(**kwargs)
        self.price_service = price_service
        Clock.schedule_once(self.start_fetch_thread, 0)

    def start_fetch_thread(self, instance=None):
        self.ids.price_label.text = 'BTC/USDT: Loading...'
        threading.Thread(target=self.fetch_price_data, daemon=True).start()

    def fetch_price_data(self):
        try:
            price = self.price_service.get_btc_usdt_price()
            Clock.schedule_once(lambda dt: self.update_ui(price))
        except Exception as e:
            print(f"UI 레이어에서 에러 처리: {e}")
            Clock.schedule_once(lambda dt: self.update_ui_error())

    def update_ui(self, price):
        self.ids.price_label.text = f"BTC/USDT: ${float(price):,.2f}"

    def update_ui_error(self):
        self.ids.price_label.text = "ERROR!"