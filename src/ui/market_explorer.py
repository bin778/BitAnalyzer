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
            unique_key = f"{data.get('exchange')}:{data.get('symbol')}"
            real_state = unique_key in self.explorer.selected_items
            self.is_checked = real_state
            if self.ids.checkbox.active != real_state:
                self.ids.checkbox.active = real_state
        return

    def on_checkbox_active(self, checkbox, value):
        if not self.explorer:
            return

        current_exchange = self.explorer.ids.exchange_spinner.text
        unique_key = f"{current_exchange}:{self.symbol}"
        is_actually_selected = unique_key in self.explorer.selected_items
        if value == is_actually_selected:
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
    selected_items = {} 

    def __init__(self, price_service, **kwargs):
        super().__init__(**kwargs)
        self.price_service = price_service
        Clock.schedule_once(lambda dt: self.load_markets('Binance'), 0.5)

    def load_markets(self, exchange_name):
        print(f"Loading markets for {exchange_name}...")
        self.raw_market_data = self.price_service.get_all_markets(exchange_name)
        self.filter_list()

    def filter_list(self):
        search_text = self.ids.search_input.text.upper()
        quote_filter = self.ids.quote_spinner.text
        current_exchange = self.ids.exchange_spinner.text
        refresh_trigger = time.time()
        
        filtered_data = []
        for market in self.raw_market_data:
            if search_text and search_text not in market['base']:
                continue
            if quote_filter != 'All' and market['quote'] != quote_filter:
                continue
            
            unique_key = f"{current_exchange}:{market['symbol']}"
            filtered_data.append({
                'symbol': market['symbol'],
                'base_coin': market['base'],
                'quote_currency': market['quote'],
                'exchange': current_exchange,
                'explorer': self,
                'is_checked': unique_key in self.selected_items,
                '_refresh_trigger': refresh_trigger
            })
            
        self.ids.rv.data = filtered_data
        self.update_selection_count()

    def toggle_selection(self, symbol, value):
        current_exchange = self.ids.exchange_spinner.text
        unique_key = f"{current_exchange}:{symbol}"
        if value:
            current_selections = list(self.selected_items.values())
            new_market = next((m for m in self.raw_market_data if m['symbol'] == symbol), None)
            if not new_market: return False
            market_to_save = new_market.copy()
            market_to_save['exchange'] = current_exchange

            if current_selections:
                first_base = current_selections[0]['base']
                if market_to_save['base'] != first_base:
                    print(f"Error: Mix matched base coins. First: {first_base}, New: {market_to_save['base']}")
                    self.show_warning(f"Only {first_base} pairs allowed!") 
                    return False

            allowed_quotes = ['KRW', 'USDT', 'USD', 'USDC', 'BUSD', 'BTC', 'ETH']
            if market_to_save['quote'] not in allowed_quotes:
                self.show_warning("Quote not supported!")
                return False

            if len(self.selected_items) >= 5:
                self.show_limit_warning() 
                return False

            self.selected_items[unique_key] = market_to_save
        else:
            if unique_key in self.selected_items:
                del self.selected_items[unique_key]
        
        self.update_selection_count()
        return True

    def show_limit_warning(self):
        self.show_warning("Max 5 Items Allowed!")

    def show_warning(self, message):
        self.ids.analyze_btn.text = message
        self.ids.analyze_btn.background_color = (1, 0.2, 0.2, 1)
        Clock.schedule_once(lambda dt: self.update_selection_count(), 1.5)

    def update_selection_count(self):
        count = len(self.selected_items)
        if count >= 5:
            self.ids.analyze_btn.background_color = (0.2, 0.6, 1, 1)
            self.ids.analyze_btn.text = f"Analyze Selected ({count}/5)"
        elif count == 0:
            self.ids.analyze_btn.background_color = (0.5, 0.5, 0.5, 1)
            self.ids.analyze_btn.text = "Select 1-5 items"
        else:
            self.ids.analyze_btn.background_color = (0.2, 0.6, 1, 1)
            self.ids.analyze_btn.text = f"Analyze Selected ({count}/5)"

    def reset_selection(self):
        print("Resetting selection (Nuke Strategy)...")
        self.selected_items.clear()
        self.ids.rv.data = []
        self.ids.rv.refresh_from_data()
        Clock.schedule_once(lambda dt: self.filter_list(), 0.1)

    def dispatch_analysis(self):
        count = len(self.selected_items)
        if 1 <= count <= 5:
            app = App.get_running_app()
            current_exchange_context = self.ids.exchange_spinner.text
            
            selected_list = list(self.selected_items.values())
            
            if hasattr(app, 'switch_to_tracker'):
                app.switch_to_tracker(current_exchange_context, selected_list)

            self.reset_selection()