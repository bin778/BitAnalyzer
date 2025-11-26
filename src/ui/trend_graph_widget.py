from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Line, Rectangle, Mesh
from kivy.metrics import dp
from kivy.uix.modalview import ModalView
from kivy.uix.button import Button
from kivy.app import App

class DetailGraphPopup(ModalView):
    def __init__(self, db_service, exchange, symbol, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.95, 0.85)
        self.auto_dismiss = True
        self.background_color = (0, 0, 0, 0.85)
        
        self.db_service = db_service
        self.price_service = App.get_running_app().price_service
        self.exchange = exchange
        self.symbol = symbol

        main_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(5))
        
        header = BoxLayout(size_hint_y=None, height=dp(40))
        title = Label(text=f"{exchange.upper()} {symbol}", font_size='18sp', bold=True, halign='left')
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
            btn.bind(on_release=lambda x, period=p: self.load_data(period))
            btn_box.add_widget(btn)
        main_layout.add_widget(btn_box)

        self.add_widget(main_layout)
        self.load_data('1D')

    def load_data(self, period):
        self.graph_widget.set_loading()
        try:
            history = self.price_service.fetch_ohlcv_history(self.exchange, self.symbol, period)
            self.graph_widget.update_graph(history, period)
        except Exception as e:
            print(f"Graph Load Error: {e}")

class TrendGraphWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        
        self.info_lbl = Label(text="Loading...", size_hint_y=0.1, markup=True)
        self.add_widget(self.info_lbl)
        self.canvas_area = GraphCanvas()
        self.add_widget(self.canvas_area)

    def set_loading(self):
        self.info_lbl.text = "Fetching Data..."
        self.canvas_area.clear_graph()

    def update_graph(self, data, period):
        if not data:
            self.info_lbl.text = "No Data Available"
            return

        prices = [d['price'] for d in data]
        highs = [d['ask'] for d in data]
        lows = [d['bid'] for d in data]
        
        curr_p = prices[-1]
        max_p = max(highs)
        min_p = min(lows)
        
        color = "55ff55" if prices[-1] >= prices[0] else "ff5555"
        self.info_lbl.text = (
            f"[{period}] Current: [b]{curr_p:,.2f}[/b] "
            f"[color={color}]({'Up' if prices[-1]>=prices[0] else 'Down'})[/color]\n"
            f"High: {max_p:,.2f} / Low: {min_p:,.2f}"
        )
        
        self.canvas_area.draw_chart(data, min_p, max_p)

class GraphCanvas(Widget):
    def clear_graph(self):
        self.canvas.clear()
        with self.canvas:
            Color(0.08, 0.08, 0.08, 1)
            Rectangle(pos=self.pos, size=self.size)

    def draw_chart(self, data, min_val, max_val):
        self.canvas.clear()
        if not data: return

        with self.canvas:
            Color(0.08, 0.08, 0.08, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            w, h = self.size
            x, y = self.pos
            count = len(data)
            x_step = w / (count - 1) if count > 1 else w
            y_range = (max_val - min_val) * 1.1 
            if y_range == 0: y_range = 1
            base_y = min_val - (y_range * 0.05)

            vertices = []
            indices = []
            
            Color(0.2, 0.6, 1, 0.3)
            for i, d in enumerate(data):
                px = x + (i * x_step)
                
                py_low = y + ((d['bid'] - base_y) / y_range * h)
                py_high = y + ((d['ask'] - base_y) / y_range * h)
                
                vertices.extend([px, py_low, 0, 0])
                vertices.extend([px, py_high, 0, 0])
                
                if i < count - 1:
                    idx = i * 2
                    indices.extend([idx, idx+1, idx+2, idx+1, idx+2, idx+3])
            
            Mesh(vertices=vertices, indices=indices, mode='triangles')

            line_pts = []
            for i, d in enumerate(data):
                px = x + (i * x_step)
                py = y + ((d['price'] - base_y) / y_range * h)
                line_pts.extend([px, py])
            
            Color(1, 1, 0, 1)
            Line(points=line_pts, width=1.5)

            py_max = y + ((max_val - base_y) / y_range * h)
            Color(1, 0.3, 0.3, 0.8)
            Line(points=[x, py_max, x+w, py_max], dash_offset=5)
            
            py_min = y + ((min_val - base_y) / y_range * h)
            Color(0.3, 1, 0.3, 0.8)
            Line(points=[x, py_min, x+w, py_min], dash_offset=5)