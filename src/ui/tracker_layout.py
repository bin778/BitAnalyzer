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

        self.ids.analysis_label.text = "K-Premium: Calculating..."
        self.ids.analysis_label.color = (0.8, 0.8, 0.8, 1)
        
        threading.Thread(target=self.fetch_data, daemon=True).start()

    def fetch_data(self):
        try:
            all_data = self.price_service.get_all_btc_order_books(limit=5)
            usdt_krw_price = self.price_service.get_usdt_krw_price()
            
            Clock.schedule_once(lambda dt: self.update_ui(all_data, usdt_krw_price))
        except Exception as e:
            print(f"전체 fetch 에러: {e}")
            Clock.schedule_once(lambda dt: self.update_ui_error())

    def update_ui(self, all_data, usdt_krw_price):
        bin_data = all_data.get('binance')
        self.ids.binance_ob.update_data('Binance', bin_data)

        upbit_data = all_data.get('upbit')
        self.ids.upbit_ob.update_data('Upbit', upbit_data)

        bybit_data = all_data.get('bybit')
        self.ids.bybit_ob.update_data('Bybit', bybit_data)
        
        self.calculate_and_display_premium(upbit_data, bin_data, usdt_krw_price)

    def calculate_and_display_premium(self, upbit_data, binance_data, usdt_krw_price):
        try:
            if not usdt_krw_price:
                raise ValueError("USDT/KRW 환율을 가져올 수 없습니다.")
                
            if 'error' in upbit_data or 'error' in binance_data:
                raise ValueError("업비트 또는 바이낸스 데이터 오류")
                
            upbit_ask = upbit_data['asks'][0][0]
            upbit_bid = upbit_data['bids'][0][0]
            upbit_mid_price = (upbit_ask + upbit_bid) / 2
            
            binance_ask = binance_data['asks'][0][0]
            binance_bid = binance_data['bids'][0][0]
            binance_mid_price = (binance_ask + binance_bid) / 2
            
            if upbit_mid_price <= 0 or binance_mid_price <= 0:
                raise ValueError("유효하지 않은 가격 데이터")

            binance_price_in_krw = binance_mid_price * usdt_krw_price
            premium_pct = ((upbit_mid_price / binance_price_in_krw) - 1) * 100
            color = (0.4, 1, 0.4, 1) if premium_pct > 0 else (1, 0.4, 0.4, 1)
            
            self.ids.analysis_label.text = (
                f"K-Premium (Upbit/Binance): {premium_pct:+.2f}% "
                f"(₩{usdt_krw_price:,.0f})"
            )
            self.ids.analysis_label.color = color

        except Exception as e:
            print(f"프리미엄 계산 에러: {e}")
            self.ids.analysis_label.text = f"K-Premium: Error ({e})"
            self.ids.analysis_label.color = (1, 0.3, 0.3, 1)

    def update_ui_error(self):
        self.ids.binance_ob.set_error_state()
        self.ids.upbit_ob.set_error_state()
        self.ids.bybit_ob.set_error_state()

        self.ids.analysis_label.text = "K-Premium: ERROR!"
        self.ids.analysis_label.color = (1, 0.3, 0.3, 1)