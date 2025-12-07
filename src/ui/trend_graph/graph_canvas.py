from datetime import datetime, timezone
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from .constants import *

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
        PAD_R, PAD_B, PAD_T = dp(60), dp(30), dp(10)

        chart_w = w - PAD_R
        chart_h_total = h - PAD_B - PAD_T
        h_price = chart_h_total * 0.75
        h_spread = chart_h_total * 0.25
        
        y_spread_start = PAD_B 
        y_price_start = PAD_B + h_spread + dp(5)
        h_price_actual = h - y_price_start - PAD_T

        now_kst = datetime.now(timezone.utc).astimezone(KST)
        end_ts = now_kst.timestamp()
        
        time_span_sec = TIME_SPAN_MAP.get(period, 86400)
        start_ts = end_ts - time_span_sec
        time_span = end_ts - start_ts

        p_diff = max(p_max - p_min, 0.000001)
        p_base = p_min - (p_diff * 0.05)
        p_range = p_diff * 1.1
        s_range = s_max * 1.2 if s_max > 0 else 1

        def get_clamped_y(val):
            rel = (val - p_base) / p_range
            y = y_price_start + (rel * h_price_actual)
            return max(y_price_start, min(y, y_price_start + h_price_actual))

        with self.canvas:
            Color(*COLOR_GRID)
            for i in range(5):
                ratio = i / 4
                py = y_price_start + (h_price_actual * ratio)
                Line(points=[0, py, chart_w, py], width=1)
                
                val = p_base + (p_range * ratio)
                lbl_text = f"{val:,.0f}" if val > 1000 else f"{val:,.2f}"
                lbl = Label(text=lbl_text, font_size='11sp', color=COLOR_TEXT,
                            size_hint=(None, None), size=(PAD_R, dp(20)), text_size=(PAD_R, dp(20)),
                            pos=(chart_w, py - dp(10)), halign='left', valign='middle')
                self.add_widget(lbl)
                self.labels.append(lbl)

            Color(0.5, 0.5, 0.5, 0.5)
            Line(points=[0, y_spread_start + h_spread, chart_w, y_spread_start + h_spread], width=1)
            
            spread_lbl = Label(text=f"Spread (Max: {s_max:.2f})", font_size='10sp', color=(0.6, 0.6, 0.7, 1),
                            size_hint=(None, None), pos=(dp(5), y_spread_start + h_spread - dp(20)))
            self.add_widget(spread_lbl)
            self.labels.append(spread_lbl)

            for ex_name, data in data_map.items():
                is_main = (ex_name == self.main_exchange)
                
                if data.get('db'):
                    prev_mid = None
                    bid_points, ask_points = [], []
                    
                    for d in data['db']:
                        if d['ts'] < start_ts or d['ts'] > end_ts + 600: continue
                        x_ratio = (d['ts'] - start_ts) / time_span
                        if not (0 <= x_ratio <= 1): continue
                        
                        px = x_ratio * chart_w
                        
                        curr_mid = (d['ask'] + d['bid']) / 2
                        if is_main:
                            if prev_mid is None: bar_color = COLOR_SPREAD_DEFAULT
                            elif curr_mid >= prev_mid: bar_color = (*COLOR_UP[:3], 0.5)
                            else: bar_color = (*COLOR_DOWN[:3], 0.5)
                            prev_mid = curr_mid
                            
                            Color(*bar_color)
                            bar_h = min((d['spread'] / s_range) * h_spread, h_spread)
                            Line(points=[px, y_spread_start, px, y_spread_start + max(1, bar_h)], width=1.2)
                            
                            bid_points.extend([px, get_clamped_y(d['bid'])])
                            ask_points.extend([px, get_clamped_y(d['ask'])])

                    if is_main and bid_points:
                        Color(*COLOR_ASK_LINE)
                        Line(points=ask_points, width=1.1)
                        Color(*COLOR_BID_LINE)
                        Line(points=bid_points, width=1.1)

                api_data = data['api']
                if not api_data: continue

                if is_main:
                    base_width = 1.0
                    if period == '1H': base_width = 2.0
                    candle_width = max(base_width, min((chart_w / (len(api_data) + 1)) * 0.7, 10.0))
                    
                    for d in api_data:
                        if d['ts'] < start_ts or d['ts'] > end_ts: continue
                        cx = ((d['ts'] - start_ts) / time_span) * chart_w
                        y_o, y_c = get_clamped_y(d['o']), get_clamped_y(d['c'])
                        y_h, y_l = get_clamped_y(d['h']), get_clamped_y(d['l'])

                        Color(*(COLOR_UP if d['c'] >= d['o'] else COLOR_DOWN))
                        Line(points=[cx, y_l, cx, y_h], width=1)
                        Rectangle(pos=(cx - candle_width/2, min(y_o, y_c)), size=(candle_width, max(1, abs(y_c - y_o))))
                else:
                    c_line = EXCHANGE_COLORS.get(ex_name, DEFAULT_COLOR)
                    Color(*c_line)
                    pts = []
                    for d in api_data:
                        if d['ts'] < start_ts or d['ts'] > end_ts: continue
                        pts.extend([((d['ts'] - start_ts) / time_span) * chart_w, get_clamped_y(d['c'])])
                    if pts: Line(points=pts, width=1.2)

            Color(*COLOR_TEXT)
            for i in range(5):
                ratio = i / 4
                ts_val = start_ts + (time_span * ratio)
                dt_obj = datetime.fromtimestamp(ts_val, KST)
                
                if period in ['1H', '1D']:
                    t_str = dt_obj.strftime("%H:%M")
                else:
                    t_str = dt_obj.strftime("%m-%d")
                    
                px = chart_w * ratio
                
                Color(0.2, 0.2, 0.2, 0.3)
                Line(points=[px, PAD_B, px, h], width=1)
                
                lbl = Label(text=t_str, font_size='10sp', color=(0.6, 0.6, 0.6, 1),
                            size_hint=(None, None), size=(dp(50), PAD_B), pos=(px - dp(25), 0))
                self.add_widget(lbl)
                self.labels.append(lbl)