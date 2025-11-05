from kivy.app import App
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.lang import Builder

from services.price_service import PriceService
from ui.tracker_layout import PriceTrackerLayout

class PriceTrackerApp(App):
    def build(self):
        Window.size = (400, 200)
        
        try:
            price_service = PriceService()
            layout = PriceTrackerLayout(price_service=price_service)
            return layout
        
        except ValueError as e:
            print(f"앱 시작 에러: {e}")
            return Label(text=f"설정 오류:\n{e}", halign='center')

if __name__ == '__main__':
    Builder.load_file('src/ui/tracker_layout.kv')
    
    PriceTrackerApp().run()