import asyncio
import logging
import websockets
import names
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
from datetime import datetime, timedelta
import aiohttp
from aiofile import async_open
from aiopath import AsyncPath

logging.basicConfig(level=logging.INFO)

class CurrencyExchange:
    BASE_URL = "https://api.privatbank.ua/p24api/exchange_rates"

    @staticmethod
    async def get_exchange_rate(date: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{CurrencyExchange.BASE_URL}?json&date={date}") as response:
                data = await response.json()
                exchange_rate = {
                    currency['currency']: currency['saleRateNB'] for currency in data['exchangeRate']
                }
                return exchange_rate

    @staticmethod
    async def get_exchange_rate_for_last_n_days(n_days):
        today = datetime.today().date()
        rates = {}
        async with aiohttp.ClientSession() as session:
            for i in range(n_days):
                date = today - timedelta(days=i)
                formatted_date = date.strftime("%d.%m.%Y")
                async with session.get(f"{CurrencyExchange.BASE_URL}?json&date={formatted_date}") as response:
                    data = await response.json()
                    exchange_rate = {
                        currency['currency']: currency['saleRateNB'] for currency in data['exchangeRate']
                    }
                    rates[date.strftime("%Y-%m-%d")] = exchange_rate
        return rates

class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def log_to_file(self, message: str):
        async with async_open("chat_logs.txt", "a") as afp:
            await afp.write(f"{datetime.now()}: {message}\n")

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            async for message in ws:
                if message.startswith("exchange"):
                    command, days_str = message.split(" ")
                    days = int(days_str)
                    await self.log_to_file(f"Command 'exchange' for {days} days")
                    await self.exchange(ws, days)
                else:
                    await self.send_to_clients(f"{ws.name}: {message}")
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def exchange(self, ws: WebSocketServerProtocol, days: int):
        exchange_rates = await CurrencyExchange.get_exchange_rate_for_last_n_days(days)
        for date, rates in exchange_rates.items():
            formatted_rate = "\n".join([f"{currency}: {rate}" for currency, rate in rates.items()])
            await ws.send(f"Exchange rates for {date}:\n{formatted_rate}")

async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())