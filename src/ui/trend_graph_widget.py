from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Line, Rectangle, Mesh
from kivy.metrics import dp
from kivy.uix.modalview import ModalView
from kivy.uix.button import Button

# TODO: 기간 별로 추세선 그래프 그리기
class DetailGraphPopup(ModalView):
    def __init__(self, db_service, exchange, symbol, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.9, 0.85)
        self.auto_dismiss = True
        self.background_color = (0, 0, 0, 0.8)
        
        self.db_service = db_service
        self.exchange = exchange
        self.symbol = symbol
        self.current_period = '1D'

        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        
        title_box = BoxLayout(size_hint_y=None, height=dp(40))
        title_label = Label(
            text=f"{exchange.upper()} - {symbol} Analysis", 
            font_size='20sp', 
            bold=True,
            halign='left',
            valign='middle'
        )
        title_label.bind(size=title_label.setter('text_size'))
        close_btn = Button(text="Close", size_hint_x=None, width=dp(80), background_color=(0.3, 0.3, 0.3, 1))
        close_btn.bind(on_release=self.dismiss)
        
        title_box.add_widget(title_label)
        title_box.add_widget(close_btn)
        layout.add_widget(title_box)

        self.graph_widget = TrendGraphWidget()
        layout.add_widget(self.graph_widget)

        btn_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        for p in ['1D', '1M', '3M', '1Y']:
            btn = Button(text=p, background_color=(0.2, 0.2, 0.2, 1))
            btn.bind(on_release=lambda instance, period=p: self.load_data(period))
            btn_box.add_widget(btn)
        layout.add_widget(btn_box)

        self.add_widget(layout)
        self.load_data('1D')

    def load_data(self, period):
        self.current_period = period
        history = self.db_service.get_price_history(self.exchange, self.symbol, period)
        self.graph_widget.update_graph(history, period)

class TrendGraphWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        
        self.info_layout = BoxLayout(size_hint_y=0.1, padding=(dp(10), 0))
        self.title_label = Label(
            text="Loading Chart Data...", 
            color=(0.8, 0.8, 0.8, 1),
            font_size='14sp',
            halign='center',
            valign='middle'
        )
        self.title_label.bind(size=self.title_label.setter('text_size'))
        self.info_layout.add_widget(self.title_label)
        self.add_widget(self.info_layout)
        self.graph_area = GraphCanvas()
        self.add_widget(self.graph_area)

    def update_graph(self, history_data, period_text):
        if not history_data:
            self.title_label.text = f"[{period_text}] No Data Available yet."
            self.graph_area.clear_graph()
            return

        prices = [d['price'] for d in history_data]
        if not prices: return

        min_val = min(prices) * 0.995
        max_val = max(prices) * 1.005
        start_p = prices[0]
        end_p = prices[-1]
        
        change = ((end_p - start_p) / start_p) * 100 if start_p else 0
        color_hex = "55ff55" if change >= 0 else "ff5555"
        
        self.title_label.text = (
            f"[{period_text}] Current: {end_p:,.0f} "
            f"([color={color_hex}]{change:+.2f}%[/color])  "
            f"High: {max_val:,.0f} / Low: {min_val:,.0f}"
        )
        self.title_label.markup = True
        
        base_color = (0.2, 0.8, 0.2, 1) if change >= 0 else (1, 0.3, 0.3, 1)
        self.graph_area.draw_filled_chart(history_data, min_val, max_val, base_color)

class GraphCanvas(Widget):
    def clear_graph(self):
        self.canvas.clear()
        with self.canvas:
            Color(0.08, 0.08, 0.08, 1)
            Rectangle(pos=self.pos, size=self.size)

    def draw_filled_chart(self, data, min_val, max_val, line_color):
        self.canvas.clear()
        if len(data) < 2: return

        with self.canvas:
            Color(0.08, 0.08, 0.08, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            Color(0.2, 0.2, 0.2, 1)
            for i in range(1, 5):
                y_pos = self.y + (self.height * (i/5))
                Line(points=[self.x, y_pos, self.right, y_pos], width=1)

            width = self.width
            height = self.height
            x_step = width / (len(data) - 1)
            val_range = max_val - min_val if max_val > min_val else 1
            
            vertices = []
            indices = []
            line_points = []

            fill_color = list(line_color)
            fill_color[3] = 0.3

            Color(*fill_color)
            
            for i, item in enumerate(data):
                price = item['price']
                
                px = self.x + (i * x_step)
                normalized_y = (price - min_val) / val_range
                py = self.y + (normalized_y * height)
                
                vertices.extend([px, self.y, 0, 0]) 
                vertices.extend([px, py, 0, 0])
                
                if i < len(data) - 1:
                    idx = i * 2
                    indices.extend([idx, idx+1, idx+2, idx+1, idx+2, idx+3])
                
                line_points.extend([px, py])

            Mesh(vertices=vertices, indices=indices, mode='triangles')

            Color(*line_color)
            Line(points=line_points, width=2)