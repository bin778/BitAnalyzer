from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.lang import Builder

from services.price_service import PriceService
from ui.tracker_layout import PriceTrackerLayout
from ui.market_explorer import MarketExplorer

class ExplorerScreen(Screen):
    def __init__(self, price_service, **kwargs):
        super().__init__(**kwargs)
        self.layout = MarketExplorer(price_service=price_service)
        self.ids['explorer_layout'] = self.layout
        self.add_widget(self.layout)
    
    def on_pre_enter(self, *args):
        if hasattr(self.layout, 'reset_selection'):
            self.layout.reset_selection()

class TrackerScreen(Screen):
    def __init__(self, price_service, **kwargs):
        super().__init__(**kwargs)
        self.layout = PriceTrackerLayout(price_service=price_service)
        self.add_widget(self.layout)
    
    def update_targets(self, exchange, selected_items):
        self.layout.update_watching_list(exchange, selected_items)

class BitAnalyzerApp(App):
    def build(self):
        Window.size = (550, 800)
        
        try:
            self.price_service = PriceService()
        except Exception as e:
            print(f"Service Init Error: {e}")
            return None

        self.sm = ScreenManager(transition=SlideTransition())
        self.explorer_screen = ExplorerScreen(name='explorer', price_service=self.price_service)
        self.tracker_screen = TrackerScreen(name='tracker', price_service=self.price_service)
        self.sm.add_widget(self.explorer_screen)
        self.sm.add_widget(self.tracker_screen)

        return self.sm

    def switch_to_tracker(self, exchange_name, selected_items):
        print(f"Switching to Tracker with: {selected_items}")
        
        self.tracker_screen.update_targets(exchange_name, selected_items)
        self.sm.transition.direction = 'left'
        self.sm.current = 'tracker'

    def switch_to_explorer(self):
        self.sm.transition.direction = 'right'
        self.sm.current = 'explorer'

# TODO: 여기서 실행 속도(데이터 수집)를 어떻게 빠르게 하면 좋을까?
# TODO: 또한 애플리케이션에서 보안 관련 이슈는 어떤 게 있을까?
if __name__ == '__main__':
    Builder.load_file('src/ui/order_book_widget.kv')
    Builder.load_file('src/ui/tracker_layout.kv')
    Builder.load_file('src/ui/market_explorer.kv')
    
    BitAnalyzerApp().run()