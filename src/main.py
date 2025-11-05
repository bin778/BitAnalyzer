import os, threading
from dotenv import load_dotenv
from binance.client import Client

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.window import Window

Window.size = (400, 200)

load_dotenv()
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
client = Client(api_key, api_secret)

class PriceTrackerLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 10

        self.price_label = Label(
            text='BTC/USDT: Waiting...',
            font_size='32sp',
            halign='center'
        )
        self.add_widget(self.price_label)

        self.refresh_button = Button(
            text='Refresh',
            size_hint=(1, 0.3)
        )
        self.refresh_button.bind(on_press=self.start_fetch_thread)
        self.add_widget(self.refresh_button)

        self.start_fetch_thread()

    def start_fetch_thread(self, instance=None):
        self.price_label.text = 'BTC/USDT: Loading...'
        threading.Thread(target=self.fetch_price_data).start()

    def fetch_price_data(self):
        try:
            ticker = client.get_ticker(symbol="BTCUSDT")
            price = ticker['lastPrice']
            Clock.schedule_once(lambda dt: self.update_ui(price))
            
        except Exception as e:
            print(f"API Error: {e}")
            Clock.schedule_once(lambda dt: self.update_ui_error())

    def update_ui(self, price):
        self.price_label.text = f"BTC/USDT: ${float(price):,.2f}"

    def update_ui_error(self):
        self.price_label.text = "ERROR!"

class PriceTrackerApp(App):
    def build(self):
        return PriceTrackerLayout()

if __name__ == '__main__':
    PriceTrackerApp().run()