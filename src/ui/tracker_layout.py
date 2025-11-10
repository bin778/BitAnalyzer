import threading, time
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

class PriceTrackerLayout(BoxLayout):
    def __init__(self, price_service, **kwargs):
        super().__init__(**kwargs)
        self.price_service = price_service
        self.running = True 
        threading.Thread(target=self.fetch_data_loop, daemon=True).start()

    def start_fetch_thread(self, instance=None):
        threading.Thread(target=self.fetch_data_once, daemon=True).start()

    def fetch_data_loop(self):
        Clock.schedule_once(lambda dt: self.set_all_loading(), 0.1)
        
        while self.running:
            try:
                all_data, usdt_krw_price = self.fetch_data_internal()
                Clock.schedule_once(lambda dt, d=all_data, p=usdt_krw_price: self.update_ui(d, p))
                time.sleep(5) 
            except Exception as e:
                print(f"fetch_data_loop 에러: {e}")
                Clock.schedule_once(lambda dt: self.update_ui_error())
                time.sleep(5)

    def fetch_data_once(self):
        self.set_all_loading()
        try:
            all_data, usdt_krw_price = self.fetch_data_internal()
            Clock.schedule_once(lambda dt: self.update_ui(all_data, usdt_krw_price))
        except Exception as e:
            print(f"fetch_data_once 에러: {e}")
            Clock.schedule_once(lambda dt: self.update_ui_error())

    def fetch_data_internal(self):
        all_data = self.price_service.get_all_btc_order_books(limit=5)
        usdt_krw_price = self.price_service.get_usdt_krw_price()
        return all_data, usdt_krw_price

    def set_all_loading(self):
        self.ids.binance_ob.set_loading_state()
        self.ids.upbit_ob.set_loading_state()
        self.ids.bybit_ob.set_loading_state()
        self.ids.analysis_label.text = "K-Premium: Calculating..."
        self.ids.analysis_label.color = (0.8, 0.8, 0.8, 1)

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
                raise ValueError("Unable to get USDT/KRW exchange rate.")
                
            if 'error' in upbit_data or 'error' in binance_data:
                raise ValueError("Binance OR Upbit Data ERROR!")
                
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
            
            self.ids.analysis_label.text = (
                f"K-Premium (Upbit/Binance): {premium_pct:+.2f}% "
                f"(₩{usdt_krw_price:,.0f})"
            )
            self.ids.analysis_label.color = color

        except Exception as e:
            print(f"K-Premium Calculation Error: {e}")
            self.ids.analysis_label.text = f"K-Premium: Error ({e})"
            self.ids.analysis_label.color = (1, 0.3, 0.3, 1)

    def update_ui_error(self):
        self.ids.binance_ob.set_error_state()
        self.ids.upbit_ob.set_error_state()
        self.ids.bybit_ob.set_error_state()
        self.ids.analysis_label.text = "K-Premium: ERROR!"
        self.ids.analysis_label.color = (1, 0.3, 0.3, 1)