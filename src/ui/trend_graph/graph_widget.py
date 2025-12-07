from datetime import datetime, timezone
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp
from .constants import *
from .graph_canvas import GraphCanvas

class TrendGraphWidget(BoxLayout):
    def __init__(self, main_exchange=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.main_exchange = main_exchange
        
        self.info_box = BoxLayout(size_hint_y=None, height=dp(25), padding=(dp(10), 0))
        self.info_lbl = Label(
            text="Initializing...", 
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
        
        if not self.active_exchanges:
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
                if isinstance(h['ts'], datetime):
                    ts_obj = h['ts'].replace(tzinfo=timezone.utc) if h['ts'].tzinfo is None else h['ts']
                    ts = ts_obj.astimezone(KST).timestamp()
                else:
                    ts_val = float(h['ts'])
                    if ts_val > 3000000000: ts_val /= 1000
                    ts = datetime.fromtimestamp(ts_val, timezone.utc).astimezone(KST).timestamp()

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
                
                if ex_name == self.main_exchange:
                    main_prices.append(h_p)
                    main_prices.append(l_p)
                all_prices.append(h_p)
                all_prices.append(l_p)

            norm_db = []
            if raw_entry.get('db'):
                for d in raw_entry['db']:
                    if isinstance(d['ts'], datetime):
                        d_ts_obj = d['ts'].replace(tzinfo=timezone.utc) if d['ts'].tzinfo is None else d['ts']
                        ts = d_ts_obj.astimezone(KST).timestamp()
                    else:
                        ts_val = float(d['ts'])
                        if ts_val > 3000000000: ts_val /= 1000
                        ts = datetime.fromtimestamp(ts_val, timezone.utc).astimezone(KST).timestamp()

                    bid = d.get('bid', 0)
                    ask = d.get('ask', 0)
                    if is_krw:
                        bid /= self.current_rate
                        ask /= self.current_rate
                    
                    spread = ask - bid if (ask > 0 and bid > 0) else 0
                    if spread > 0:
                        norm_db.append({'ts': ts, 'spread': spread, 'bid': bid, 'ask': ask})

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
            p_max, p_min = max(main_prices), min(main_prices)
        elif all_prices:
            p_max, p_min = max(all_prices), min(all_prices)
        else:
            p_max, p_min = 1, 0

        all_spreads = [d['spread'] for v in visible_data.values() for d in v['db']]
        s_max = max(all_spreads) if all_spreads else 0

        self.info_lbl.text = "  |  ".join(info_texts)
        self.canvas_area.draw_chart(visible_data, p_min, p_max, s_max, self.current_period)