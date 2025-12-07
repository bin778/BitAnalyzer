import asyncio
from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Line

from services.analysis_service import calculate_k_premium
from ui.trend_graph import DetailGraphPopup

class PriceTrackerLayout(BoxLayout):
    def __init__(self, price_service, db_service=None, **kwargs):
        super().__init__(**kwargs)
        self.price_service = price_service
        self.db_service = db_service
        
        self.tracking_task = None
        self.active_targets = []
        self.selected_slot_key = None
        
        self.widget_map = {
            f'slot_{i}': getattr(self.ids, f'slot_{i}') for i in range(10)
        }
        self.k_premium_data = {'upbit': None, 'binance': None}

        for key, widget in self.widget_map.items():
            widget.bind(on_touch_down=lambda w, touch, k=key: self.on_slot_touch(k, touch))

    def on_slot_touch(self, key, touch):
        widget = self.widget_map.get(key)
        if widget.collide_point(*touch.pos):
            target = next((t for t in self.active_targets if t['key'] == key), None)
            if target:
                self.select_slot(key)
                self.show_popup(target)
            return True
        return False
    
    def open_trend_popup(self):
        target = None
        if self.selected_slot_key:
            target = next((t for t in self.active_targets if t['key'] == self.selected_slot_key), None)
        
        if not target and self.active_targets:
            target = self.active_targets[0]
            self.select_slot(target['key'])

        if target:
            self.show_popup(target)

    def show_popup(self, target):
        if not self.db_service:
            print("DB Service is not available.")
            return

        popup = DetailGraphPopup(
            db_service=self.db_service, 
            exchange=target['exchange'], 
            symbol=target['symbol']
        )
        popup.open()

    def select_slot(self, key):
        self.selected_slot_key = key
        for k, widget in self.widget_map.items():
            widget.canvas.after.clear()
        
        sel = self.widget_map.get(key)
        if sel:
            with sel.canvas.after:
                Color(1, 1, 0, 1)
                Line(rectangle=(sel.x, sel.y, sel.width, sel.height), width=2)

    def update_watching_list(self, exchange_name_ignored, selected_items):
        if self.tracking_task:
            self.tracking_task.cancel()
            self.tracking_task = None

        self.active_targets = []
        self.selected_slot_key = None
        keys = [f'slot_{i}' for i in range(10)]
        
        for i, item in enumerate(selected_items[:10]):
            target_exchange = item.get('exchange', exchange_name_ignored)
            self.active_targets.append({
                'key': keys[i],
                'exchange': target_exchange,
                'symbol': item['symbol']
            })
            
        active_keys = [t['key'] for t in self.active_targets]
        
        for key, widget in self.widget_map.items():
            widget.canvas.after.clear()
            if key not in active_keys:
                widget.ids.title_label.text = "Empty"
                widget._set_ob_labels("-")

        if self.active_targets:
            self.tracking_task = asyncio.create_task(self.start_tracking_loop())

    async def start_tracking_loop(self):
        try:
            while True:
                await self.fetch_and_update()
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            print("Tracking loop stopped.")
        except Exception as e:
            print(f"Tracking Loop Error: {e}")

    async def fetch_and_update(self):
        tasks = []
        
        for target in self.active_targets:
            ex = target['exchange']
            sym = target['symbol']
            
            tasks.append(self.price_service.get_btc_order_book(ex, sym))
            tasks.append(self.price_service.get_ticker(ex, sym))

        tasks.append(self.price_service.get_usdt_krw_price())

        results = await asyncio.gather(*tasks, return_exceptions=True)

        usdt_krw_price = results[-1]
        if isinstance(usdt_krw_price, Exception): usdt_krw_price = None

        data_map = {}
        for i, target in enumerate(self.active_targets):
            idx = i * 2
            ob_res = results[idx]
            ticker_res = results[idx+1]
            
            if isinstance(ob_res, Exception): ob_res = {'error': str(ob_res)}
            if isinstance(ticker_res, Exception): ticker_res = {'error': str(ticker_res)}

            data_map[target['key']] = {
                'ob': ob_res,
                'ticker': ticker_res
            }

        self.update_ui(data_map, usdt_krw_price)

    def set_all_loading(self):
        pass 

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
                
                if last_price and not isinstance(last_price, str):
                    bids = ob.get('bids', [])
                    asks = ob.get('asks', [])
                    best_bid = bids[0][0] if bids else 0
                    best_ask = asks[0][0] if asks else 0
                    
                    if self.db_service:
                        try:
                            self.db_service.save_spread(
                                target['exchange'], 
                                target['symbol'], 
                                best_bid, 
                                best_ask
                            )
                        except Exception as e:
                            print(f"DB Save Error: {e}")

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