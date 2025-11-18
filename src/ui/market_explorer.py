from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.clock import Clock

class MarketItemRow(RecycleDataViewBehavior, BoxLayout):
    symbol = StringProperty("")
    base_coin = StringProperty("")
    quote_currency = StringProperty("")
    selected = BooleanProperty(False)
    index = None

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # TODO: 여기서 클릭 시 해당 마켓의 상세 정보(호가창 등)로 이동하는 로직 추가 예정
            print(f"Selected: {self.symbol}")
            return True
        return super().on_touch_down(touch)

class MarketExplorer(BoxLayout):
    raw_market_data = []

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
        
        filtered_data = []
        
        for market in self.raw_market_data:
            if search_text and search_text not in market['base']:
                continue
                
            if quote_filter != 'All' and market['quote'] != quote_filter:
                continue
                
            filtered_data.append({
                'symbol': market['symbol'],
                'base_coin': market['base'],
                'quote_currency': market['quote']
            })
            
        self.ids.rv.data = filtered_data
        print(f"Filtered result: {len(filtered_data)} markets found.")