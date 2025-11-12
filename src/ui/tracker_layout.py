import threading, time
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from services.analysis_service import calculate_k_premium

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
                all_data, usdt_krw_price = self.fetch_data_internal_parallel()
                Clock.schedule_once(lambda dt, d=all_data, p=usdt_krw_price: self.update_ui(d, p))
                time.sleep(5) 
            except Exception as e:
                print(f"fetch_data_loop 에러: {e}")
                Clock.schedule_once(lambda dt: self.update_ui_error())
                time.sleep(5)

    def fetch_data_once(self):
        self.set_all_loading()
        try:
            all_data, usdt_krw_price = self.fetch_data_internal_parallel()
            Clock.schedule_once(lambda dt: self.update_ui(all_data, usdt_krw_price))
        except Exception as e:
            print(f"fetch_data_once 에러: {e}")
            Clock.schedule_once(lambda dt: self.update_ui_error())

    def fetch_data_internal_parallel(self):
        results = {}
        threads = []

        def fetch_binance():
            results['binance'] = self.price_service.get_btc_order_book('binance', 'BTC/USDT', limit=5)
        def fetch_upbit():
            results['upbit'] = self.price_service.get_btc_order_book('upbit', 'BTC/KRW', limit=5)        
        def fetch_bybit():
            results['bybit'] = self.price_service.get_btc_order_book('bybit', 'BTC/USDT', limit=5)
        def fetch_usdt_krw():
            results['usdt_krw'] = self.price_service.get_usdt_krw_price()

        threads.append(threading.Thread(target=fetch_binance))
        threads.append(threading.Thread(target=fetch_upbit))
        threads.append(threading.Thread(target=fetch_bybit))
        threads.append(threading.Thread(target=fetch_usdt_krw))

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        all_data = {
            'binance': results.get('binance'),
            'upbit': results.get('upbit'),
            'bybit': results.get('bybit'),
        }
        usdt_krw_price = results.get('usdt_krw')
        
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
        
        premium_result = calculate_k_premium(upbit_data, bin_data, usdt_krw_price)
        self.ids.analysis_label.text = premium_result['text']
        self.ids.analysis_label.color = premium_result['color']

    def update_ui_error(self):
        self.ids.binance_ob.set_error_state()
        self.ids.upbit_ob.set_error_state()
        self.ids.bybit_ob.set_error_state()
        self.ids.analysis_label.text = "K-Premium: ERROR!"
        self.ids.analysis_label.color = (1, 0.3, 0.3, 1)