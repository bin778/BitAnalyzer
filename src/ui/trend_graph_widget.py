import asyncio
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Line, Rectangle, Mesh
from kivy.metrics import dp
from kivy.uix.modalview import ModalView
from kivy.uix.button import Button
from kivy.app import App

EXCHANGE_COLORS = {
    'Binance': (1, 0.84, 0, 1),    # Gold
    'Upbit': (0.12, 0.56, 1, 1),   # Blue
    'Bybit': (1, 0.6, 0.2, 1),     # Orange
    'Bitfinex': (0.2, 0.8, 0.2, 1),# Green
    'Kucoin': (0.6, 0.4, 0.8, 1)   # Purple
}
DEFAULT_COLOR = (0.8, 0.8, 0.8, 1)

class DetailGraphPopup(ModalView):
    def __init__(self, db_service, exchange, symbol, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.95, 0.85)
        self.auto_dismiss = True
        self.background_color = (0, 0, 0, 0.9)
        
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
                self.compare_targets.append({'exchange': t['exchange'], 'symbol': t['symbol']})

        main_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(5))
        
        header = BoxLayout(size_hint_y=None, height=dp(40))
        title_text = f"{exchange.upper()} {symbol}"
        if len(self.compare_targets) > 1:
            title_text += f" vs {len(self.compare_targets)-1} Others"
            
        title = Label(text=title_text, font_size='18sp', bold=True, halign='left')
        title.bind(size=title.setter('text_size'))
        close = Button(text="X", size_hint_x=None, width=dp(40), background_color=(0.3,0.3,0.3,1))
        close.bind(on_release=self.dismiss)
        header.add_widget(title)
        header.add_widget(close)
        main_layout.add_widget(header)

        self.graph_widget = TrendGraphWidget()
        main_layout.add_widget(self.graph_widget)

        btn_box = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        for p in ['1D', '1M', '3M', '1Y']:
            btn = Button(text=p, background_color=(0.2, 0.2, 0.2, 1))
            btn.bind(on_release=lambda x, period=p: self.trigger_load(period))
            btn_box.add_widget(btn)
        main_layout.add_widget(btn_box)

        self.add_widget(main_layout)
        self.trigger_load('1D')

    def trigger_load(self, period):
        asyncio.create_task(self.load_data_async(period))

    async def load_data_async(self, period):
        self.graph_widget.set_loading()
        try:
            tasks = []
            for target in self.compare_targets:
                tasks.append(self.price_service.fetch_ohlcv_history(target['exchange'], target['symbol'], period))
            
            results = await asyncio.gather(*tasks)
            
            combined_data = {}
            for i, target in enumerate(self.compare_targets):
                ex_name = target['exchange']
                history = results[i]
                if history:
                    combined_data[ex_name] = history
            
            self.graph_widget.update_graph(combined_data, period)
            
        except Exception as e:
            print(f"Graph Load Error: {e}")

class TrendGraphWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        
        self.info_lbl = Label(text="Loading...", size_hint_y=0.1, markup=True, font_size='14sp')
        self.add_widget(self.info_lbl)
        
        self.canvas_area = GraphCanvas()
        self.add_widget(self.canvas_area)

    def set_loading(self):
        self.info_lbl.text = "Fetching Data..."
        self.canvas_area.clear_graph()

    def update_graph(self, data_map, period):
        if not data_map:
            self.info_lbl.text = "No Data Available"
            return

        all_prices = []
        last_prices_info = []

        for ex_name, history in data_map.items():
            prices = [d['price'] for d in history]
            all_prices.extend(prices)
            
            curr = prices[-1]
            start = prices[0]
            color_hex = "55ff55" if curr >= start else "ff5555"
            ex_color = EXCHANGE_COLORS.get(ex_name, DEFAULT_COLOR)
            ex_color_hex = "".join([f"{int(c*255):02x}" for c in ex_color[:3]])
            
            last_prices_info.append(
                f"[color={ex_color_hex}]{ex_name}[/color]: [b]{curr:,.2f}[/b] ([color={color_hex}]{'Up' if curr>=start else 'Down'}[/color])"
            )

        global_max = max(all_prices)
        global_min = min(all_prices)
        
        self.info_lbl.text = f"[{period}] " + "  |  ".join(last_prices_info)
        self.canvas_area.draw_chart(data_map, global_min, global_max, period)

class GraphCanvas(RelativeLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.labels = []

    def clear_graph(self):
        self.canvas.clear()
        for lbl in self.labels:
            self.remove_widget(lbl)
        self.labels.clear()
        
        with self.canvas:
            Color(0.08, 0.08, 0.08, 1)
            Rectangle(pos=(0, 0), size=self.size)

    def draw_chart(self, data_map, min_val, max_val, period):
        self.clear_graph()
        if not data_map: return

        w, h = self.size
        padding_left = dp(50)
        padding_bottom = dp(20)
        chart_w = w - padding_left - dp(10)
        chart_h = h - padding_bottom - dp(10)

        first_key = list(data_map.keys())[0]
        count = len(data_map[first_key])
        x_step = chart_w / (count - 1) if count > 1 else chart_w
        
        y_range = (max_val - min_val) * 1.1 
        if y_range == 0: y_range = 1
        base_y = min_val - (y_range * 0.05)

        with self.canvas:
            Color(0.08, 0.08, 0.08, 1)
            Rectangle(pos=(0, 0), size=self.size)
            
            Color(0.3, 0.3, 0.3, 0.5)
            steps = 5
            for i in range(steps):
                price = min_val + (max_val - min_val) * (i / (steps - 1))
                py = padding_bottom + ((price - base_y) / y_range * chart_h)
                
                Line(points=[padding_left, py, w, py], dash_offset=4, dash_length=4)
                
                lbl = Label(
                    text=f"{price:,.0f}", 
                    font_size='10sp', 
                    color=(0.7, 0.7, 0.7, 1),
                    size_hint=(None, None), 
                    size=(padding_left, dp(20)),
                    pos=(0, py - dp(10)),
                    halign='right', valign='middle'
                )
                self.add_widget(lbl)
                self.labels.append(lbl)

            x_steps = 4
            first_data = data_map[first_key]
            for i in range(x_steps):
                idx = int((count - 1) * (i / (x_steps - 1)))
                if idx < len(first_data):
                    d = first_data[idx]
                    ts = d['ts']
                    
                    if period == '1D':
                        t_str = ts.strftime("%H:%M")
                    elif period == '1M':
                        t_str = ts.strftime("%m-%d")
                    else:
                        t_str = ts.strftime("%Y-%m")

                    px = padding_left + (idx * x_step)
                    
                    Line(points=[px, padding_bottom, px, h], dash_offset=4, dash_length=4)
                    
                    lbl = Label(
                        text=t_str, 
                        font_size='10sp', 
                        color=(0.7, 0.7, 0.7, 1),
                        size_hint=(None, None), 
                        size=(dp(40), padding_bottom),
                        pos=(px - dp(20), 0),
                        halign='center', valign='middle'
                    )
                    self.add_widget(lbl)
                    self.labels.append(lbl)

            is_single_graph = len(data_map) == 1
            
            for ex_name, data in data_map.items():
                if not data: continue
                
                line_pts = []
                c = EXCHANGE_COLORS.get(ex_name, DEFAULT_COLOR)
                
                if is_single_graph:
                    Color(c[0], c[1], c[2], 0.2)
                    vertices = []
                    indices = []
                    for i, d in enumerate(data):
                        px = padding_left + (i * x_step)
                        py_base = padding_bottom
                        py_val = padding_bottom + ((d['price'] - base_y) / y_range * chart_h)
                        
                        vertices.extend([px, py_base, 0, 0])
                        vertices.extend([px, py_val, 0, 0])
                        
                        if i < len(data) - 1:
                            idx = i * 2
                            indices.extend([idx, idx+1, idx+2, idx+1, idx+2, idx+3])
                    Mesh(vertices=vertices, indices=indices, mode='triangles')

                for i, d in enumerate(data):
                    px = padding_left + (i * x_step)
                    py = padding_bottom + ((d['price'] - base_y) / y_range * chart_h)
                    line_pts.extend([px, py])
                
                line_width = 1.5 if is_single_graph else 2.0
                Color(c[0], c[1], c[2], 1)
                Line(points=line_pts, width=line_width)

                if not is_single_graph and line_pts:
                    last_x = line_pts[-2]
                    last_y = line_pts[-1]
                    lbl = Label(
                        text=ex_name,
                        font_size='10sp',
                        color=c,
                        size_hint=(None, None),
                        size=(dp(50), dp(20)),
                        pos=(last_x - dp(50), last_y + dp(5))
                    )
                    self.add_widget(lbl)
                    self.labels.append(lbl)