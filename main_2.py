import aiohttp
import asyncio
from datetime import datetime, timedelta

class CurrencyRatesAPI:
    BASE_URL = "https://api.privatbank.ua/p24api/exchange_rates"

    async def fetch_rates(self, date):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.BASE_URL}?json&date={date}", ssl=False) as response:
                return await response.json()

    async def get_currency_rates_for_last_n_days(self, n_days, additional_currencies=None):
        additional_currencies = additional_currencies or []
        today = datetime.today().date()
        rates = {}
        for i in range(n_days):
            date = today - timedelta(days=i)
            formatted_date = date.strftime("%d.%m.%Y")
            data = await self.fetch_rates(formatted_date)
            currency_rates = {
                currency["currency"]: currency["saleRateNB"] for currency in data["exchangeRate"]
            }
            rates[date] = {**currency_rates}
        return rates

class CurrencyRatesConsoleUtility:
    def __init__(self):
        self.api = CurrencyRatesAPI()

    async def run(self, n_days, additional_currencies=None):
        try:
            if n_days > 10:
                raise ValueError("Number of days should not exceed 10.")
                
            rates = await self.api.get_currency_rates_for_last_n_days(n_days, additional_currencies)
            for date, currencies in rates.items():
                print(f"Date: {date}")
                for currency, rate in currencies.items():
                    print(f"{currency}: {rate}")
                print()
        except ValueError as ve:
            print(f"Error: {ve}")
        except aiohttp.ClientError as ce:
            print(f"Network error: {ce}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

async def main():
    utility = CurrencyRatesConsoleUtility()
    await utility.run(10, ["USD", "EUR", "GBP"])  # Retrieve rates for the last 10 days with additional currencies

if __name__ == "__main__":
    asyncio.run(main())