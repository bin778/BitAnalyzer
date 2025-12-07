import asyncio
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.modalview import ModalView
from kivy.metrics import dp
from kivy.app import App

from .constants import *
from .graph_widget import TrendGraphWidget

class DetailGraphPopup(ModalView):
    def __init__(self, db_service, exchange, symbol, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.98, 0.98)
        self.auto_dismiss = True
        self.background_color = COLOR_BG
        self.overlay_color = (0, 0, 0, 0.9)
        
        self.db_service = db_service
        self.price_service = App.get_running_app().price_service
        self.main_exchange = exchange
        self.symbol = symbol
        
        self.update_task = None
        self.is_open = True
        self.current_period = '1H'

        app = App.get_running_app()
        try:
            tracker_layout = app.root.get_screen('tracker').layout
            self.compare_targets = [{'exchange': exchange, 'symbol': symbol}]
            
            current_base = symbol.split('/')[0]
            for t in tracker_layout.active_targets:
                t_base = t['symbol'].split('/')[0]
                if t['exchange'] != exchange and t_base == current_base:
                    self.compare_targets.append(t)
        except:
            self.compare_targets = [{'exchange': exchange, 'symbol': symbol}]

        main_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(5))
        
        header = BoxLayout(size_hint_y=None, height=dp(40))
        title = Label(text=f"{exchange.upper()} {symbol} Analysis", font_size='18sp', 
                    bold=True, halign='left', color=COLOR_TEXT)
        title.bind(size=title.setter('text_size'))
        
        close_btn = Button(text="X", size_hint_x=None, width=dp(40), 
                        background_normal='', background_color=(0.2, 0.2, 0.2, 1), font_size='18sp')
        close_btn.bind(on_release=self.dismiss)
        
        header.add_widget(title)
        header.add_widget(close_btn)
        main_layout.add_widget(header)

        self.toggle_layout = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(5))
        main_layout.add_widget(self.toggle_layout)

        graph_wrapper = BoxLayout(padding=dp(2))
        self.graph_widget = TrendGraphWidget(main_exchange=self.main_exchange)
        graph_wrapper.add_widget(self.graph_widget)
        main_layout.add_widget(graph_wrapper)

        btn_box = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(2))
        for p in ['1H', '1D', '1M', '3M', '1Y']:
            btn = Button(text=p, background_normal='', background_color=(0.15, 0.15, 0.2, 1),
                        color=COLOR_TEXT, font_size='13sp')
            btn.bind(on_release=lambda x, period=p: self.change_period(period))
            btn_box.add_widget(btn)
        main_layout.add_widget(btn_box)

        self.add_widget(main_layout)
        self.init_toggles()
        
        self.trigger_load(self.current_period)
        self.start_auto_refresh()

    def init_toggles(self):
        self.toggle_layout.clear_widgets()
        for target in self.compare_targets:
            ex_name = target['exchange']
            btn = ToggleButton(
                text=ex_name, size_hint_x=0.2, state='down',
                background_normal='', background_color=(0.15, 0.15, 0.2, 1),
                font_size='12sp', bold=True
            )
            btn.color = EXCHANGE_COLORS.get(ex_name, DEFAULT_COLOR)
            btn.bind(on_press=lambda instance, ex=ex_name: self.on_toggle(ex, instance.state))
            self.toggle_layout.add_widget(btn)

    def on_toggle(self, exchange_name, state):
        self.graph_widget.set_visibility(exchange_name, state == 'down')

    def change_period(self, period):
        self.current_period = period
        self.graph_widget.set_loading()

    def trigger_load(self, period):
        asyncio.create_task(self.load_data_async(period, silent=False))

    def start_auto_refresh(self):
        self.update_task = asyncio.create_task(self.auto_refresh_loop())

    async def auto_refresh_loop(self):
        while self.is_open:
            try:
                await self.load_data_async(self.current_period, silent=True)
            except Exception as e:
                print(f"Auto refresh error: {e}")
            
            await asyncio.sleep(1.5)

    def on_dismiss(self):
        self.is_open = False
        if self.update_task:
            self.update_task.cancel()
        super().on_dismiss()

    async def load_data_async(self, period, silent=False):
        if not silent:
            self.graph_widget.set_loading()
            
        try:
            self.usdt_krw_rate = await self.price_service.get_usdt_krw_price() or 1400.0
            loop = asyncio.get_event_loop()
            
            api_tasks = [self.price_service.fetch_ohlcv_history(t['exchange'], t['symbol'], period) for t in self.compare_targets]
            api_results = await asyncio.gather(*api_tasks)

            combined_data = {}
            for i, target in enumerate(self.compare_targets):
                ex_name = target['exchange']
                
                db_history = await loop.run_in_executor(
                    None, self.db_service.get_spread_history, ex_name, target['symbol'], period
                )
                
                combined_data[ex_name] = {
                    'symbol': target['symbol'],
                    'api': api_results[i], 
                    'db': db_history       
                }
            
            self.graph_widget.update_graph(combined_data, period, self.usdt_krw_rate)
        except Exception as e:
            print(f"Graph Load Error: {e}")
            self.graph_widget.info_lbl.text = f"Error: {str(e)}"