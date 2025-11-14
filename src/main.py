from kivy.app import App
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.lang import Builder

from services.price_service import PriceService
from ui.tracker_layout import PriceTrackerLayout

class PriceTrackerApp(App):
    def build(self):
        Window.size = (900, 600)
        
        try:
            price_service = PriceService()
            self.layout = PriceTrackerLayout(price_service=price_service)
            return self.layout
        
        except ValueError as e:
            print(f"Application Starting Error: {e}")
            return Label(text=f"Setting Error:\n{e}", halign='center', size_hint=(1, 1))

    def on_stop(self):
        print("Application Exit... Stop Thread.")
        if hasattr(self, 'layout'):
            self.layout.running = False 

if __name__ == '__main__':
    Builder.load_file('src/ui/order_book_widget.kv')
    Builder.load_file('src/ui/tracker_layout.kv')
    
    PriceTrackerApp().run()