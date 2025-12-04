import asyncio
from datetime import datetime, timedelta, timezone
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.modalview import ModalView
from kivy.graphics import Color, Line, Rectangle, ScissorPush, ScissorPop
from kivy.metrics import dp
from kivy.app import App

COLOR_BG = (0.05, 0.05, 0.08, 1)
COLOR_GRID = (0.3, 0.3, 0.35, 0.5)
COLOR_TEXT = (0.85, 0.85, 0.85, 1)
COLOR_UP = (0.1, 0.85, 0.5, 1)
COLOR_DOWN = (1.0, 0.3, 0.35, 1)
COLOR_SPREAD = (0.3, 0.4, 0.5, 0.3)

KST = timezone(timedelta(hours=9))

EXCHANGE_COLORS = {
    'Binance': (0.95, 0.75, 0.06, 1),
    'Upbit': (0.05, 0.36, 0.65, 1),
    'Bybit': (1, 0.6, 0.2, 1),
    'Bitfinex': (0.2, 0.8, 0.2, 1),
    'Kucoin': (0.6, 0.4, 0.8, 1)
}
DEFAULT_COLOR = (0.5, 0.5, 0.5, 1)

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

        app = App.get_running_app()
        tracker_layout = app.root.get_screen('tracker').layout
        
        self.compare_targets = [{'exchange': exchange, 'symbol': symbol}]
        
        current_base = symbol.split('/')[0]
        for t in tracker_layout.active_targets:
            t_base = t['symbol'].split('/')[0]
            if t['exchange'] != exchange and t_base == current_base:
                self.compare_targets.append(t)
        
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
        for p in ['1D', '1M', '3M', '1Y']:
            btn = Button(text=p, background_normal='', background_color=(0.15, 0.15, 0.2, 1),
                        color=COLOR_TEXT, font_size='13sp')
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
                text=ex_name, size_hint_x=0.2, state='down',
                background_normal='', background_color=(0.15, 0.15, 0.2, 1),
                font_size='12sp', bold=True
            )
            btn.color = EXCHANGE_COLORS.get(ex_name, DEFAULT_COLOR)
            btn.bind(on_press=lambda instance, ex=ex_name: self.on_toggle(ex, instance.state))
            self.toggle_layout.add_widget(btn)

    def on_toggle(self, exchange_name, state):
        self.graph_widget.set_visibility(exchange_name, state == 'down')

    def trigger_load(self, period):
        asyncio.create_task(self.load_data_async(period))

    async def load_data_async(self, period):
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
                    None, self.db_service.get_price_history, ex_name, target['symbol'], period
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

class TrendGraphWidget(BoxLayout):
    def __init__(self, main_exchange=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.main_exchange = main_exchange
        
        self.info_box = BoxLayout(size_hint_y=None, height=dp(25), padding=(dp(10), 0))
        self.info_lbl = Label(
            text="Waiting for data...", 
            font_size='14sp', 
            color=COLOR_TEXT,
            halign='left', valign='middle',
            markup=True
        )
        self.info_lbl.bind(size=self.info_lbl.setter('text_size'))
        self.info_box.add_widget(self.info_lbl)
        self.add_widget(self.info_box)
        
        self.canvas_area = GraphCanvas(main_exchange=self.main_exchange)
        self.add_widget(self.canvas_area)
        
        self.raw_data_map = {}
        self.active_exchanges = set()
        self.current_period = '1D'
        self.current_rate = 1400.0

    def set_loading(self):
        self.info_lbl.text = "Loading Chart..."
        self.canvas_area.clear_graph()

    def set_visibility(self, exchange_name, is_active):
        if is_active: self.active_exchanges.add(exchange_name)
        else: self.active_exchanges.discard(exchange_name)
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
        info_texts = []
        
        main_prices = [] 
        all_prices = []

        for ex_name in self.active_exchanges:
            if ex_name not in self.raw_data_map: continue
            
            raw_entry = self.raw_data_map[ex_name]
            is_krw = 'KRW' in raw_entry['symbol']
            
            norm_api = []
            prev_close = None
            
            for h in raw_entry['api']:
                ts = h['ts'].timestamp() if isinstance(h['ts'], datetime) else float(h['ts'])
                if ts > 3000000000: ts /= 1000 

                c_p = h['price']
                h_p = h.get('high', c_p)
                l_p = h.get('low', c_p)
                o_p = h.get('open', prev_close if prev_close else c_p)
                prev_close = c_p

                if is_krw:
                    c_p /= self.current_rate
                    h_p /= self.current_rate
                    l_p /= self.current_rate
                    o_p /= self.current_rate

                norm_api.append({'ts': ts, 'o': o_p, 'h': h_p, 'l': l_p, 'c': c_p})
                
                # 메인 거래소 가격 별도 수집
                if ex_name == self.main_exchange:
                    main_prices.append(h_p)
                    main_prices.append(l_p)
                
                all_prices.append(h_p)
                all_prices.append(l_p)

            norm_db = []
            for d in raw_entry['db']:
                ts = d['ts'].timestamp() if isinstance(d['ts'], datetime) else float(d['ts'])
                if ts > 3000000000: ts /= 1000
                
                bid = d.get('bid', 0)
                ask = d.get('ask', 0)
                if is_krw:
                    bid /= self.current_rate
                    ask /= self.current_rate
                
                spread = ask - bid if (ask > 0 and bid > 0) else 0
                if spread > 0:
                    norm_db.append({'ts': ts, 'spread': spread})

            visible_data[ex_name] = {'api': norm_api, 'db': norm_db}

            if norm_api:
                last_p = norm_api[-1]['c']
                ex_color = EXCHANGE_COLORS.get(ex_name, DEFAULT_COLOR)
                hex_col = "".join([f"{int(c*255):02x}" for c in ex_color[:3]])
                info_texts.append(f"[color={hex_col}]{ex_name}[/color] [b]${last_p:,.2f}[/b]")

        if not visible_data:
            self.info_lbl.text = "No Data Available"
            self.canvas_area.clear_graph()
            return

        if main_prices:
            p_max = max(main_prices)
            p_min = min(main_prices)
        elif all_prices:
            p_max = max(all_prices)
            p_min = min(all_prices)
        else:
            p_max = 1
            p_min = 0

        all_spreads = [d['spread'] for v in visible_data.values() for d in v['db']]
        s_max = max(all_spreads) if all_spreads else 0

        self.info_lbl.text = "  |  ".join(info_texts)
        self.canvas_area.draw_chart(visible_data, p_min, p_max, s_max, self.current_period)

class GraphCanvas(RelativeLayout):
    def __init__(self, main_exchange=None, **kwargs):
        super().__init__(**kwargs)
        self.labels = []
        self.main_exchange = main_exchange

    def clear_graph(self):
        self.canvas.clear()
        for lbl in self.labels:
            self.remove_widget(lbl)
        self.labels.clear()
        with self.canvas:
            Color(*COLOR_BG)
            Rectangle(pos=(0, 0), size=self.size)

    def draw_chart(self, data_map, p_min, p_max, s_max, period):
        self.clear_graph()
        if not data_map: return

        w, h = self.size
        
        PAD_R = dp(60)
        PAD_B = dp(30)
        PAD_T = dp(10)

        chart_w = w - PAD_R
        chart_h_total = h - PAD_B - PAD_T
        
        h_price = chart_h_total * 0.75
        h_spread = chart_h_total * 0.25
        
        y_spread_start = PAD_B 
        y_price_start = PAD_B + h_spread + dp(5)
        
        h_price_actual = h - y_price_start - PAD_T

        now_kst = datetime.now(timezone.utc).astimezone(KST)
        end_ts = now_kst.timestamp()
        
        if period == '1D':
            time_span_sec = 24 * 3600
        elif period == '1M':
            time_span_sec = 30 * 24 * 3600
        elif period == '3M':
            time_span_sec = 90 * 24 * 3600
        elif period == '1Y':
            time_span_sec = 365 * 24 * 3600
        else:
            time_span_sec = 24 * 3600
            
        start_ts = end_ts - time_span_sec
        time_span = end_ts - start_ts

        p_diff = p_max - p_min
        if p_diff == 0: p_diff = 1
        p_base = p_min - (p_diff * 0.05)
        p_range = (p_diff * 1.1)
        s_range = s_max * 1.2 if s_max > 0 else 1

        with self.canvas:
            Color(*COLOR_GRID)
            steps = 5
            for i in range(steps):
                ratio = i / (steps - 1)
                py = y_price_start + (h_price_actual * ratio)
                
                Line(points=[0, py, chart_w, py], width=1)
                
                val = p_base + (p_range * ratio)
                lbl_text = f"{val:,.0f}" if val > 1000 else f"{val:,.2f}"
                
                lbl = Label(
                    text=lbl_text,
                    font_size='11sp', 
                    color=COLOR_TEXT,
                    size_hint=(None, None),
                    size=(PAD_R, dp(20)),
                    text_size=(PAD_R, dp(20)),
                    pos=(chart_w, py - dp(10)),
                    halign='left',
                    valign='middle'
                )
                self.add_widget(lbl)
                self.labels.append(lbl)

            Color(0.5, 0.5, 0.5, 0.5)
            Line(points=[0, y_spread_start + h_spread, chart_w, y_spread_start + h_spread], width=1)

            spread_lbl = Label(
                text="Spread (Ask-Bid)", 
                font_size='10sp', 
                color=(0.6, 0.6, 0.7, 1),
                size_hint=(None, None), 
                size=(dp(100), dp(20)),
                pos=(dp(5), y_spread_start + h_spread - dp(20)),
                halign='left', 
                valign='middle'
            )
            self.add_widget(spread_lbl)
            self.labels.append(spread_lbl)

            for ex_name, data in data_map.items():
                is_main = (ex_name == self.main_exchange)
                
                if data['db']:
                    if is_main: Color(*COLOR_SPREAD)
                    else: Color(0.3, 0.3, 0.3, 0.2)
                    
                    for d in data['db']:
                        if d['ts'] < start_ts or d['ts'] > end_ts: continue
                        
                        x_ratio = (d['ts'] - start_ts) / time_span
                        px = x_ratio * chart_w
                        
                        bar_h = min((d['spread'] / s_range) * h_spread, h_spread)
                        Line(points=[px, y_spread_start, px, y_spread_start + bar_h], width=1.1)

                api_data = data['api']
                if not api_data: continue

                def get_clamped_y(val):
                    rel = (val - p_base) / p_range
                    y = y_price_start + (rel * h_price_actual)
                    return max(y_price_start, min(y, y_price_start + h_price_actual))

                if is_main:
                    candle_width = (chart_w / (len(api_data) + 1)) * 0.7
                    if candle_width < 1: candle_width = 1.0
                    
                    for d in api_data:
                        if d['ts'] < start_ts or d['ts'] > end_ts: continue

                        x_ratio = (d['ts'] - start_ts) / time_span
                        cx = x_ratio * chart_w
                        
                        y_o = get_clamped_y(d['o'])
                        y_c = get_clamped_y(d['c'])
                        y_h = get_clamped_y(d['h'])
                        y_l = get_clamped_y(d['l'])

                        is_up = d['c'] >= d['o']
                        Color(*(COLOR_UP if is_up else COLOR_DOWN))

                        Line(points=[cx, y_l, cx, y_h], width=1)
                        rect_h = abs(y_c - y_o)
                        if rect_h < 1: rect_h = 1
                        Rectangle(pos=(cx - candle_width/2, min(y_o, y_c)), size=(candle_width, rect_h))
                else:
                    c_line = EXCHANGE_COLORS.get(ex_name, DEFAULT_COLOR)
                    Color(*c_line)
                    pts = []
                    for d in api_data:
                        if d['ts'] < start_ts or d['ts'] > end_ts: continue

                        x_ratio = (d['ts'] - start_ts) / time_span
                        px = x_ratio * chart_w
                        py = get_clamped_y(d['c'])
                        
                        pts.extend([px, py])
                    if pts:
                        Line(points=pts, width=1.2)

            Color(*COLOR_TEXT)
            time_steps = 5
            for i in range(time_steps):
                ratio = i / (time_steps - 1)
                ts_val = start_ts + (time_span * ratio)
                dt_kst = datetime.fromtimestamp(ts_val, KST)
                
                t_str = dt_kst.strftime("%H:%M") if period == '1D' else dt_kst.strftime("%m-%d")
                px = chart_w * ratio
                
                Color(0.2, 0.2, 0.2, 0.3)
                Line(points=[px, PAD_B, px, h], width=1)
                
                lbl = Label(
                    text=t_str, 
                    font_size='10sp',
                    color=(0.6, 0.6, 0.6, 1),
                    size_hint=(None, None),
                    size=(dp(50), PAD_B),
                    text_size=(dp(50), PAD_B),
                    pos=(px - dp(25), 0),
                    halign='center',
                    valign='top'
                )
                self.add_widget(lbl)
                self.labels.append(lbl)