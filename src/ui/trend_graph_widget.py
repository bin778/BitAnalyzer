import asyncio
from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.uix.modalview import ModalView
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.app import App

# TODO: 시간 위치 맨 아래로 이동하기
# TODO: DB 호가 데이터 한국 시간대와 맞게 만들기(현재 영국 시간대에 있음)
# TODO: Bitfinex가 다른 코인와 혼자 튀는 문제 해결
# TODO: 밑의 막대 그래프(거래량?)의 단위도 추가할 것
COLOR_UP = (0.05, 0.8, 0.5, 1)
COLOR_DOWN = (0.96, 0.27, 0.36, 1)

# 거래소별 테마 색상 (라인 차트용)
EXCHANGE_COLORS = {
    'Binance': (1, 0.84, 0, 1),    # Gold
    'Upbit': (0.9, 0.9, 0.9, 1),   # White (어두운 배경에서 잘 보이게)
    'Bybit': (1, 0.6, 0.2, 1),     # Orange
    'Bitfinex': (0.2, 0.8, 0.2, 1),# Green
    'Kucoin': (0.6, 0.4, 0.8, 1)   # Purple
}
DEFAULT_COLOR = (0.7, 0.7, 0.7, 1)

class DetailGraphPopup(ModalView):
    def __init__(self, db_service, exchange, symbol, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.95, 0.95)
        self.auto_dismiss = True
        self.background_color = (0.05, 0.05, 0.05, 1)
        
        self.db_service = db_service
        self.price_service = App.get_running_app().price_service
        self.main_exchange = exchange
        self.symbol = symbol

        app = App.get_running_app()
        tracker_layout = app.root.get_screen('tracker').layout
        
        self.compare_targets = []
        self.compare_targets.append({'exchange': exchange, 'symbol': symbol})
        
        current_base = symbol.split('/')[0]
        for t in tracker_layout.active_targets:
            t_base = t['symbol'].split('/')[0]
            if t['exchange'] != exchange and t_base == current_base:
                self.compare_targets.append(t)

        main_layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        
        header = BoxLayout(size_hint_y=None, height=dp(40))
        
        title_txt = f"{exchange.upper()} {symbol}"
        title = Label(text=title_txt, font_size='20sp', bold=True, 
                    halign='left', valign='middle', color=(1,1,1,1))
        title.bind(size=title.setter('text_size'))
        
        close_btn = Button(text="X", size_hint_x=None, width=dp(40), 
                        background_normal='', background_color=(0.2, 0.2, 0.2, 1),
                        font_size='18sp')
        close_btn.bind(on_release=self.dismiss)
        
        header.add_widget(title)
        header.add_widget(close_btn)
        main_layout.add_widget(header)

        self.toggle_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        main_layout.add_widget(self.toggle_layout)

        graph_bg = BoxLayout(orientation='vertical')
        self.graph_widget = TrendGraphWidget(main_exchange=self.main_exchange)
        graph_bg.add_widget(self.graph_widget)
        main_layout.add_widget(graph_bg)

        btn_box = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(5))
        periods = ['1D', '1M', '3M', '1Y']
        for p in periods:
            btn = Button(text=p, background_normal='', background_color=(0.15, 0.15, 0.15, 1),
                        color=(0.8, 0.8, 0.8, 1), font_size='14sp')
            btn.bind(on_release=lambda x, period=p: self.trigger_load(period))
            btn_box.add_widget(btn)
        main_layout.add_widget(btn_box)

        self.add_widget(main_layout)
        
        self.init_toggles()
        self.trigger_load('1D')

    def init_toggles(self):
        self.toggle_layout.clear_widgets()
        for target in self.compare_targets:
            ex_name = target['exchange']
            btn = ToggleButton(
                text=ex_name, 
                size_hint_x=0.3,
                state='down',
                background_normal='',
                background_color=(0.15, 0.15, 0.15, 1),
                group=None
            )

            c = EXCHANGE_COLORS.get(ex_name, DEFAULT_COLOR)
            btn.color = c
            btn.bind(on_press=lambda instance, ex=ex_name: self.on_toggle(ex, instance.state))
            self.toggle_layout.add_widget(btn)

    def on_toggle(self, exchange_name, state):
        is_active = (state == 'down')
        self.graph_widget.set_visibility(exchange_name, is_active)

    def trigger_load(self, period):
        asyncio.create_task(self.load_data_async(period))

    async def load_data_async(self, period):
        self.graph_widget.set_loading()
        try:
            self.usdt_krw_rate = await self.price_service.get_usdt_krw_price() or 1400.0
            
            loop = asyncio.get_event_loop()
            combined_data = {}
            
            api_tasks = []
            for target in self.compare_targets:
                api_tasks.append(self.price_service.fetch_ohlcv_history(target['exchange'], target['symbol'], period))
            api_results = await asyncio.gather(*api_tasks)

            for i, target in enumerate(self.compare_targets):
                ex_name = target['exchange']
                symbol = target['symbol']
                db_history = await loop.run_in_executor(
                    None, 
                    self.db_service.get_price_history, 
                    ex_name, symbol, period
                )
                combined_data[ex_name] = {
                    'symbol': symbol,
                    'api_history': api_results[i], 
                    'db_history': db_history       
                }
            
            self.graph_widget.update_graph(combined_data, period, self.usdt_krw_rate)
            
        except Exception as e:
            print(f"Graph Load Error: {e}")
            self.graph_widget.info_lbl.text = f"Error: {str(e)}"

class TrendGraphWidget(BoxLayout):
    def __init__(self, main_exchange=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.main_exchange = main_exchange
        
        self.info_lbl = Label(text="Initializing...", size_hint_y=None, height=dp(30), 
                            markup=True, font_size='14sp', halign='left')
        self.info_lbl.bind(size=self.info_lbl.setter('text_size'))
        self.add_widget(self.info_lbl)
        
        self.canvas_area = GraphCanvas(main_exchange=self.main_exchange)
        self.add_widget(self.canvas_area)
        
        self.raw_data_map = {}
        self.active_exchanges = set()
        self.current_period = '1D'
        self.current_rate = 1400.0

    def set_loading(self):
        self.info_lbl.text = "[color=ffff00]Loading Data...[/color]"
        self.canvas_area.clear_graph()

    def set_visibility(self, exchange_name, is_active):
        if is_active:
            self.active_exchanges.add(exchange_name)
        else:
            if exchange_name in self.active_exchanges:
                self.active_exchanges.remove(exchange_name)
        self.redraw_with_filter()

    def update_graph(self, data_map, period, rate):
        self.raw_data_map = data_map
        self.current_period = period
        self.current_rate = rate

        self.active_exchanges = set(data_map.keys())
        self.redraw_with_filter()

    def redraw_with_filter(self):
        if not self.raw_data_map: return

        visible_data = {}
        all_highs = [] 
        all_lows = []
        all_spreads = []    
        last_info = []

        global_start_ts = None
        global_end_ts = None

        for ex_name in self.active_exchanges:
            if ex_name not in self.raw_data_map: continue
            
            entry = self.raw_data_map[ex_name]
            symbol = entry['symbol']
            is_krw = 'KRW' in symbol
            
            api_hist = entry.get('api_history', [])
            norm_api = []
            
            prev_close = None

            for h in api_hist:
                ts = h['ts'].timestamp() if isinstance(h['ts'], datetime) else float(h['ts'])
                if ts > 3000000000: ts /= 1000

                if global_start_ts is None or ts < global_start_ts: global_start_ts = ts
                if global_end_ts is None or ts > global_end_ts: global_end_ts = ts

                close_p = float(h['price'])
                high_p = float(h.get('high', close_p))
                low_p = float(h.get('low', close_p))
                open_p = float(h.get('open', prev_close if prev_close else close_p))
                prev_close = close_p

                if is_krw:
                    close_p /= self.current_rate
                    high_p /= self.current_rate
                    low_p /= self.current_rate
                    open_p /= self.current_rate
                
                norm_api.append({
                    'ts': ts, 'open': open_p, 'high': high_p, 'low': low_p, 'close': close_p
                })
                all_highs.append(high_p)
                all_lows.append(low_p)

            db_hist = entry.get('db_history', [])
            norm_db = []
            for h in db_hist:
                ts = h['ts'].timestamp() if isinstance(h['ts'], datetime) else float(h['ts'])
                if ts > 3000000000: ts /= 1000

                bid = float(h.get('bid', 0))
                ask = float(h.get('ask', 0))
                if is_krw:
                    bid /= self.current_rate
                    ask /= self.current_rate
                
                spread = ask - bid if (ask > 0 and bid > 0) else 0
                if spread > 0:
                    norm_db.append({'ts': ts, 'spread': spread})
                    all_spreads.append(spread)

            visible_data[ex_name] = {'api': norm_api, 'db': norm_db}

            if norm_api:
                last_p = norm_api[-1]['close']
                ex_color = EXCHANGE_COLORS.get(ex_name, DEFAULT_COLOR)
                ex_hex = "".join([f"{int(c*255):02x}" for c in ex_color[:3]])
                last_info.append(f"[color={ex_hex}]{ex_name}[/color] [b]${last_p:,.2f}[/b]")

        if not all_highs or global_start_ts is None:
            self.canvas_area.clear_graph()
            self.info_lbl.text = "No Data available for selected exchanges."
            return

        p_max = max(all_highs)
        p_min = min(all_lows)
        s_max = max(all_spreads) if all_spreads else 0
        
        self.info_lbl.text = "  |  ".join(last_info)
        
        self.canvas_area.draw_chart(
            visible_data, p_min, p_max, s_max, 
            global_start_ts, global_end_ts, self.current_period
        )

class GraphCanvas(RelativeLayout):
    def __init__(self, main_exchange=None, **kwargs):
        super().__init__(**kwargs)
        self.labels = []
        self.main_exchange = main_exchange

    def clear_graph(self):
        self.canvas.clear()
        for lbl in self.labels: self.remove_widget(lbl)
        self.labels.clear()
        with self.canvas:
            Color(0.08, 0.08, 0.08, 1)
            Rectangle(pos=(0, 0), size=self.size)

    def draw_chart(self, data_map, p_min, p_max, s_max, start_ts, end_ts, period):
        self.clear_graph()
        if not data_map: return

        w, h = self.size
        pad_l = dp(10)
        pad_r = dp(60)
        pad_b = dp(30)
        pad_t = dp(10)

        chart_w = w - pad_l - pad_r
        chart_h = h - pad_b - pad_t
        
        h_price = chart_h * 0.75
        h_spread = chart_h * 0.20
        y_spread_base = pad_b 
        y_price_base = pad_b + h_spread + (chart_h * 0.05)

        time_span = end_ts - start_ts
        if time_span == 0: time_span = 1

        p_range = (p_max - p_min) * 1.05
        if p_range == 0: p_range = 1
        p_base_val = p_min - (p_range * 0.025)

        s_range = s_max * 1.1 if s_max > 0 else 1

        with self.canvas:
            Color(0.2, 0.2, 0.2, 1)
            
            steps = 6
            for i in range(steps):
                ratio = i / (steps - 1)
                py = y_price_base + (h_price * ratio)
                Line(points=[pad_l, py, pad_l + chart_w, py], width=1)
                
                price_val = p_base_val + (p_range * ratio)
                lbl = Label(
                    text=f"{price_val:,.2f}", 
                    font_size='11sp', 
                    color=(0.6, 0.6, 0.6, 1),
                    size_hint=(None, None),
                    size=(pad_r, dp(20)),
                    pos=(w - pad_r, py - dp(10)),
                    halign='left', valign='middle'
                )
                self.add_widget(lbl)
                self.labels.append(lbl)

            Color(0.3, 0.3, 0.3, 1)
            Line(points=[pad_l, y_spread_base + h_spread, pad_l + chart_w, y_spread_base + h_spread], width=1)
            
            for ex_name, data in data_map.items():
                is_main = (ex_name == self.main_exchange)
                
                c_bar = EXCHANGE_COLORS.get(ex_name, DEFAULT_COLOR)
                Color(c_bar[0], c_bar[1], c_bar[2], 0.8)
                
                for d in data['db']:
                    x_ratio = (d['ts'] - start_ts) / time_span
                    if 0 <= x_ratio <= 1:
                        px = pad_l + (x_ratio * chart_w)
                        bar_h = (d['spread'] / s_range) * h_spread
                        Line(points=[px, y_spread_base, px, y_spread_base + bar_h], width=1.5)

                if is_main:
                    candle_width = max(1, (chart_w / len(data['api'])) * 0.6)
                    
                    for d in data['api']:
                        x_ratio = (d['ts'] - start_ts) / time_span
                        if not (0 <= x_ratio <= 1): continue
                        
                        px = pad_l + (x_ratio * chart_w)
                        
                        y_o = y_price_base + ((d['open'] - p_base_val) / p_range * h_price)
                        y_c = y_price_base + ((d['close'] - p_base_val) / p_range * h_price)
                        y_h = y_price_base + ((d['high'] - p_base_val) / p_range * h_price)
                        y_l = y_price_base + ((d['low'] - p_base_val) / p_range * h_price)
                        
                        is_up = d['close'] >= d['open']
                        c = COLOR_UP if is_up else COLOR_DOWN
                        Color(c[0], c[1], c[2], 1)
                        
                        Line(points=[px, y_l, px, y_h], width=1)
                        rect_h = abs(y_c - y_o)
                        if rect_h < 1: rect_h = 1
                        rect_y = min(y_o, y_c)
                        Rectangle(pos=(px - candle_width/2, rect_y), size=(candle_width, rect_h))

                else:
                    c_line = EXCHANGE_COLORS.get(ex_name, DEFAULT_COLOR)
                    Color(c_line[0], c_line[1], c_line[2], 1)
                    line_pts = []
                    for d in data['api']:
                        x_ratio = (d['ts'] - start_ts) / time_span
                        if 0 <= x_ratio <= 1:
                            px = pad_l + (x_ratio * chart_w)
                            py = y_price_base + ((d['close'] - p_base_val) / p_range * h_price)
                            line_pts.extend([px, py])
                    if line_pts:
                        Line(points=line_pts, width=1.2)

            Color(0.6, 0.6, 0.6, 1)
            time_steps = 5
            for i in range(time_steps):
                ratio = i / (time_steps - 1)
                ts_val = start_ts + (time_span * ratio)
                
                dt = datetime.fromtimestamp(ts_val)
                t_str = dt.strftime("%H:%M") if period == '1D' else dt.strftime("%m-%d")
                
                px = pad_l + (chart_w * ratio)
                
                Line(points=[px, y_spread_base, px, y_spread_base - dp(5)], width=1)
                
                lbl = Label(text=t_str, font_size='10sp', color=(0.7,0.7,0.7,1),
                            pos=(px - dp(20), 0), size=(dp(40), pad_b),
                            halign='center', valign='top')
                self.add_widget(lbl)
                self.labels.append(lbl)