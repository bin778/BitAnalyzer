from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Line, Rectangle

class TrendGraphWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        
        self.title_label = Label(
            text="Price Trend (No Data)", 
            size_hint_y=0.1, 
            color=(0.7, 0.7, 0.7, 1),
            font_size='12sp'
        )
        self.add_widget(self.title_label)
        
        self.graph_area = GraphCanvas()
        self.add_widget(self.graph_area)

    def update_graph(self, points, period_text):
        if not points:
            self.title_label.text = f"{period_text}: No Data Available"
            self.graph_area.clear_graph()
            return

        prices = [p[1] for p in points]
        min_p, max_p = min(prices), max(prices)
        start_p, end_p = prices[0], prices[-1]
        
        change_pct = ((end_p - start_p) / start_p) * 100 if start_p != 0 else 0
        color = (1, 0.3, 0.3, 1) if change_pct < 0 else (0.2, 0.8, 0.2, 1)
        
        self.title_label.text = f"{period_text} Trend: {change_pct:+.2f}% (High: {max_p:,.0f} / Low: {min_p:,.0f})"
        self.title_label.color = color
        
        self.graph_area.draw_line_graph(points, min_p, max_p, color)

class GraphCanvas(Widget):
    def clear_graph(self):
        self.canvas.clear()

    def draw_line_graph(self, points, min_val, max_val, line_color):
        self.canvas.clear()
        if len(points) < 2: return

        with self.canvas:
            Color(0.12, 0.12, 0.12, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            Color(0.3, 0.3, 0.3, 0.5)
            Line(points=[self.x, self.center_y, self.right, self.center_y], dash_offset=5)
            
            graph_points = []
            width = self.width
            height = self.height
            x_step = width / (len(points) - 1)
            val_range = max_val - min_val if max_val != min_val else 1

            for i, (_, price) in enumerate(points):
                px = self.x + (i * x_step)
                
                normalized_y = (price - min_val) / val_range
                py = self.y + (height * 0.05) + (normalized_y * (height * 0.9))
                
                graph_points.extend([px, py])

            Color(*line_color)
            Line(points=graph_points, width=1.5)