import time
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty, ListProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.app import App
from kivy.clock import Clock

class MarketItemRow(RecycleDataViewBehavior, BoxLayout):
    symbol = StringProperty("")
    base_coin = StringProperty("")
    quote_currency = StringProperty("")
    is_checked = BooleanProperty(False)
    index = None
    explorer = ObjectProperty(None) 

    def refresh_view_attrs(self, rv, index, data):
        super().refresh_view_attrs(rv, index, data)
        self.index = index
        self.explorer = data.get('explorer')
        
        if self.explorer:
            real_state = data.get('symbol') in self.explorer.selected_symbols
            
            self.is_checked = real_state
            
            if self.ids.checkbox.active != real_state:
                self.ids.checkbox.active = real_state
        return

    def on_checkbox_active(self, checkbox, value):
        if not self.explorer:
            return

        is_actually_in_set = self.symbol in self.explorer.selected_symbols
        if value == is_actually_in_set:
            return

        success = self.explorer.toggle_selection(self.symbol, value)
        
        if not success and value:
            Clock.schedule_once(lambda dt: setattr(checkbox, 'active', False))

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not self.ids.checkbox.collide_point(*touch.pos):
            self.ids.checkbox.active = not self.ids.checkbox.active
            return True
        return super().on_touch_down(touch)


class MarketExplorer(BoxLayout):
    raw_market_data = ListProperty([])
    selected_symbols = set()

    def __init__(self, price_service, **kwargs):
        super().__init__(**kwargs)
        self.price_service = price_service
        Clock.schedule_once(lambda dt: self.load_markets('Binance'), 0.5)

    def load_markets(self, exchange_name):
        print(f"Loading markets for {exchange_name}...")
        self.raw_market_data = self.price_service.get_all_markets(exchange_name)
        self.selected_symbols.clear()
        self.filter_list()

    def filter_list(self):
        search_text = self.ids.search_input.text.upper()
        quote_filter = self.ids.quote_spinner.text
        
        refresh_trigger = time.time()
        
        filtered_data = []
        for market in self.raw_market_data:
            if search_text and search_text not in market['base']:
                continue
            if quote_filter != 'All' and market['quote'] != quote_filter:
                continue
            
            filtered_data.append({
                'symbol': market['symbol'],
                'base_coin': market['base'],
                'quote_currency': market['quote'],
                'explorer': self,
                'is_checked': market['symbol'] in self.selected_symbols,
                '_refresh_trigger': refresh_trigger
            })
            
        self.ids.rv.data = filtered_data
        self.update_selection_count()

    def toggle_selection(self, symbol, value):
        if value:
            current_selections = [
                m for m in self.raw_market_data if m['symbol'] in self.selected_symbols
            ]
            
            new_market = next((m for m in self.raw_market_data if m['symbol'] == symbol), None)
            
            # [규칙 1] Base Coin 통일 로직
            if current_selections and new_market:
                first_base = current_selections[0]['base']
                
                if new_market['base'] != first_base:
                    print(f"Error: You must select the same base coin ({first_base}).")
                    self.show_warning(f"Only {first_base} pairs allowed!") 
                    return False

            # [규칙 2] Quote Coin 제한 (K-Premium 및 메이저 마켓 허용)
            allowed_quotes = ['KRW', 'USDT', 'USD', 'USDC', 'BUSD', 'BTC', 'ETH']
            
            if new_market and new_market['quote'] not in allowed_quotes:
                print(f"Error: Quote {new_market['quote']} is not supported for comparison.")
                self.show_warning("Quote not supported!")
                return False

            # [규칙 3] 3개 까지 선택
            if len(self.selected_symbols) >= 3:
                if symbol not in self.selected_symbols:
                    self.show_limit_warning() 
                    return False
            self.selected_symbols.add(symbol)
        else:
            self.selected_symbols.discard(symbol)
        
        self.update_selection_count()
        return True

    def show_limit_warning(self):
        print("Maximum selection reached (3 items).")
        self.show_warning("Max 3 Items Allowed!")

    def show_warning(self, message):
        self.ids.analyze_btn.text = message
        self.ids.analyze_btn.background_color = (1, 0.2, 0.2, 1)
        Clock.schedule_once(lambda dt: self.update_selection_count(), 1.5)

    def update_selection_count(self):
        count = len(self.selected_symbols)
        if count >= 3:
            self.ids.analyze_btn.background_color = (0.2, 0.6, 1, 1)
            self.ids.analyze_btn.text = f"Analyze Selected ({count}/3)"
        elif count == 0:
            self.ids.analyze_btn.background_color = (0.5, 0.5, 0.5, 1)
            self.ids.analyze_btn.text = "Select 1-3 items"
        else:
            self.ids.analyze_btn.background_color = (0.2, 0.6, 1, 1)
            self.ids.analyze_btn.text = f"Analyze Selected ({count}/3)"

    def reset_selection(self):
        print("Resetting selection (Nuke Strategy)...")
        self.selected_symbols.clear()
        
        self.ids.rv.data = []
        self.ids.rv.refresh_from_data()
        
        Clock.schedule_once(lambda dt: self.filter_list(), 0.1)

    def dispatch_analysis(self):
        count = len(self.selected_symbols)
        if 1 <= count <= 3:
            app = App.get_running_app()
            exchange_name = self.ids.exchange_spinner.text
            
            selected_items = [
                m for m in self.raw_market_data if m['symbol'] in self.selected_symbols
            ]
            
            if hasattr(app, 'switch_to_tracker'):
                app.switch_to_tracker(exchange_name, selected_items)

            self.reset_selection()