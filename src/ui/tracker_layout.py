import threading
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from .order_book_widget import OrderBookWidget

# TODO: 실시간 시세 업데이트 기능 추가(Multi-Thread)
class PriceTrackerLayout(BoxLayout):
    def __init__(self, price_service, **kwargs):
        super().__init__(**kwargs)
        self.price_service = price_service
        Clock.schedule_once(self.start_fetch_thread, 0.5)

    def start_fetch_thread(self, instance=None):
        self.ids.binance_ob.set_loading_state()
        self.ids.upbit_ob.set_loading_state()
        self.ids.bybit_ob.set_loading_state()
        
        threading.Thread(target=self.fetch_data, daemon=True).start()

    def fetch_data(self):
        try:
            all_data = self.price_service.get_all_btc_order_books(limit=5)
            Clock.schedule_once(lambda dt: self.update_ui(all_data))
        except Exception as e:
            print(f"전체 fetch 에러: {e}")
            Clock.schedule_once(lambda dt: self.update_ui_error())

    def update_ui(self, all_data):
        bin_data = all_data.get('binance')
        self.ids.binance_ob.update_data('Binance', bin_data)

        upbit_data = all_data.get('upbit')
        self.ids.upbit_ob.update_data('Upbit', upbit_data)

        bybit_data = all_data.get('bybit')
        self.ids.bybit_ob.update_data('Bybit', bybit_data)

    def update_ui_error(self):
        self.ids.binance_ob.set_error_state()
        self.ids.upbit_ob.set_error_state()
        self.ids.bybit_ob.set_error_state()