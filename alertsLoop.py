import asyncio
import aiohttp
import time
import keyboard
import ctypes  # An included library with Python install.
import winsound
import requests

class AlertsLoop:
    def __init__(self, filename, api_key, telegram_token, chat_id):
        self.filename = filename
        self.api_key = api_key
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.running = True
        self.triggered_alerts = []
        self.currencies = []
        self.Symboles = []
        self.lst2 = []
        self.load_data()

    def load_data(self):
        try:
            with open(self.filename, "r") as saveFile:
                data = saveFile.read()
                self.currencies = list(filter(None, data.split(";")))
                self.lst2 = []
                if not len(self.currencies) == 0:
                    for i in range(len(self.currencies)):
                        data1 = self.currencies[i].split(" : ")
                        data2 = data1[1].split(" = ")
                        name = data1[0]
                        symbol = data2[0]
                        price = data2[1]
                        self.Symboles.append(symbol)
                        self.lst2.append(price)
                else:
                    print("There are no active alerts, please add new alerts before running this bot.")
                    self.running = False
        except FileNotFoundError:
            print(f"File {self.filename} not found.")
            self.running = False

    async def get_price(self, session, currency, index):
        url = self.api_key + currency
        async with session.get(url) as response:
            data = await response.json()
            if float(data['price']) < float(self.lst2[index]):
                close_price = float(self.lst2[index]) + (float(self.lst2[index]) * 0.2 / 100)
                if float(data['price']) <= close_price and float(data['price']) >= float(self.lst2[index]) and not data['symbol'] in self.triggered_alerts:
                    self.triggered_alerts.append(data['symbol'])
                    self.currencies.pop(index)
                    message = f"Alert Triggered: {data['symbol']} price is {data['price']}"
                    url2 = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage?chat_id={self.chat_id}&text={message}"
                    print(requests.get(url2).json())
                    with open(self.filename, "w") as saveFile:
                        for y in self.currencies:
                            saveFile.write(y + ';')
            else:
                close_price = float(self.lst2[index]) - (float(self.lst2[index]) * 0.2 / 100)
                if float(data['price']) >= close_price and float(data['price']) <= float(self.lst2[index]) and not data['symbol'] in self.triggered_alerts:
                    self.triggered_alerts.append(data['symbol'])
                    print(self.currencies)
                    self.currencies.pop(index)
                    message = f"Alert Triggered: {data['symbol']} price is {data['price']}"
                    url2 = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage?chat_id={self.chat_id}&text={message}"
                    print(requests.get(url2).json())
                    with open(self.filename, "w") as saveFile:
                        for y in self.currencies:
                            saveFile.write(y + ';')
            
                #winsound.Beep(1000, 3000)
                # ctypes.windll.user32.MessageBoxW(0, f"{data['symbol']} price is {data['price']}", "Alert Triggered", 1)

    async def get_prices(self):
        async with aiohttp.ClientSession() as session:
            tasks = [self.get_price(session, currency, index) for index, currency in enumerate(self.Symboles)]
            await asyncio.gather(*tasks)

    async def main_loop(self):
        while self.running:
            await self.get_prices()
            await asyncio.sleep(2)

    def start_loop(self):
        asyncio.run(self.main_loop())

    def stop_loop(self):
        self.running = False
