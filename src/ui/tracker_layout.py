import threading, time
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.app import App
from services.analysis_service import calculate_k_premium
from services.database_service import DatabaseService
from datetime import datetime

class PriceTrackerLayout(BoxLayout):
    def __init__(self, price_service, **kwargs):
        super().__init__(**kwargs)
        self.price_service = price_service
        self.db_service = DatabaseService()
        
        self.running = False 
        self.active_targets = []
        self.current_graph_period = '1D'
        
        self.widget_map = {
            'slot_0': self.ids.slot_0,
            'slot_1': self.ids.slot_1,
            'slot_2': self.ids.slot_2,
            'slot_3': self.ids.slot_3,
            'slot_4': self.ids.slot_4
        }
        
        self.k_premium_data = {'upbit': None, 'binance': None}

        threading.Thread(target=self.fetch_data_loop, daemon=True).start()

    def update_watching_list(self, exchange_name_ignored, selected_items):
        self.running = False
        time.sleep(0.05)
        
        self.active_targets = []
        keys = ['slot_0', 'slot_1', 'slot_2', 'slot_3', 'slot_4']
        
        for i, item in enumerate(selected_items[:5]):
            target_exchange = item.get('exchange', exchange_name_ignored)
            self.active_targets.append({
                'key': keys[i],
                'exchange': target_exchange,
                'symbol': item['symbol']
            })
            
        active_keys = [t['key'] for t in self.active_targets]
        for key, widget in self.widget_map.items():
            if key not in active_keys:
                widget.ids.title_label.text = "Empty"
                widget._set_ob_labels("-")

        self.running = True
        self.fetch_data_once()
        
        if self.active_targets:
            self.update_graph_period(self.current_graph_period)

    def update_graph_period(self, period):
        self.current_graph_period = period
        if not self.active_targets: return
        
        target = self.active_targets[0]
        
        threading.Thread(target=self._fetch_graph_history, args=(target['exchange'], target['symbol'], period), daemon=True).start()

    def _fetch_graph_history(self, exchange, symbol, period):
        history = self.db_service.get_price_history(exchange, symbol, period)
        Clock.schedule_once(lambda dt: self.ids.trend_graph.update_graph(history, period))

    def fetch_data_loop(self):
        while True: 
            if self.running:
                try:
                    all_data, usdt_krw_price = self.fetch_data_internal_parallel()
                    Clock.schedule_once(lambda dt, d=all_data, p=usdt_krw_price: self.update_ui(d, p))
                    time.sleep(5) 
                except Exception as e:
                    print(f"fetch_data_loop Error: {e}")
                    time.sleep(5)
            else:
                time.sleep(0.5)

    def fetch_data_once(self):
        if not self.running:
            return
        
        self.set_all_loading()
        threading.Thread(target=self._fetch_and_update_once, daemon=True).start()

    def _fetch_and_update_once(self):
        try:
            all_data, usdt_krw_price = self.fetch_data_internal_parallel()
            Clock.schedule_once(lambda dt, d=all_data, p=usdt_krw_price: self.update_ui(d, p))
        except Exception as e:
            print(f"fetch_data_once Error: {e}")

    def fetch_data_internal_parallel(self):
        results = {}
        threads = []

        if not self.active_targets:
            return {}, None

        for target in self.active_targets:
            key = target['key']
            ex = target['exchange']
            sym = target['symbol']
            
            def fetch_ob(k=key, e=ex, s=sym):
                results[f"{k}_ob"] = self.price_service.get_btc_order_book(e, s)
            def fetch_ticker(k=key, e=ex, s=sym):
                results[f"{k}_ticker"] = self.price_service.get_ticker(e, s)
            
            threads.append(threading.Thread(target=fetch_ob, daemon=True))
            threads.append(threading.Thread(target=fetch_ticker, daemon=True))

        def fetch_usdt_krw():
            results['usdt_krw'] = self.price_service.get_usdt_krw_price()
        threads.append(threading.Thread(target=fetch_usdt_krw, daemon=True))

        for t in threads: t.start()
        for t in threads: t.join()

        all_data = {}
        for target in self.active_targets:
            key = target['key']
            all_data[key] = {
                'ob': results.get(f"{key}_ob"),
                'ticker': results.get(f"{key}_ticker")
            }
        return all_data, results.get('usdt_krw')

    def set_all_loading(self):
        for target in self.active_targets:
            key = target['key']
            if key in self.widget_map:
                self.widget_map[key].set_loading_state()
        self.ids.analysis_label.text = "Updating..."

    def update_ui(self, all_data, usdt_krw_price):
        self.k_premium_data = {'upbit': None, 'binance': None}

        for target in self.active_targets:
            key = target['key']
            data = all_data.get(key)
            widget = self.widget_map.get(key)
            
            if widget and data:
                display_exchange = target['exchange'].capitalize()
                widget.update_data(display_exchange, data)
                
                ticker = data.get('ticker', {})
                ob = data.get('ob', {})
                last_price = ticker.get('last')
                
                if last_price:
                    bids = ob.get('bids', [])
                    asks = ob.get('asks', [])
                    best_bid = bids[0][0] if bids else None
                    best_ask = asks[0][0] if asks else None
                    
                    self.db_service.save_ticker(
                        target['exchange'], 
                        target['symbol'], 
                        last_price, 
                        best_bid, 
                        best_ask
                    )
                
                if 'KRW' in target['symbol']:
                    if self.k_premium_data['upbit'] is None:
                        self.k_premium_data['upbit'] = data.get('ob')
                elif 'USDT' in target['symbol']:
                    if self.k_premium_data['binance'] is None:
                        self.k_premium_data['binance'] = data.get('ob')

        upbit_data = self.k_premium_data['upbit']
        bin_data = self.k_premium_data['binance']
        
        if upbit_data and bin_data and usdt_krw_price:
            premium_result = calculate_k_premium(upbit_data, bin_data, usdt_krw_price)
            self.ids.analysis_label.text = premium_result['text']
            self.ids.analysis_label.color = premium_result['color']
        else:
            self.ids.analysis_label.text = "Kimchi Premium (Select KRW & USDT markets)"
            self.ids.analysis_label.color = (0.5, 0.5, 0.5, 1)

        self.ids.timestamp_label.text = f"Last Updated: {datetime.now().strftime('%H:%M:%S')}"

    def update_ui_error(self):
        for target in self.active_targets:
            key = target['key']
            if key in self.widget_map:
                self.widget_map[key].set_error_state()
        self.ids.analysis_label.text = "Data Fetch Error!"
        self.ids.analysis_label.color = (1, 0.3, 0.3, 1)
        self.ids.timestamp_label.text = "Last Updated: ERROR"