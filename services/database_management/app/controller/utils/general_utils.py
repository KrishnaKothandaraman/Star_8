import asyncio
import json
import time
from typing import List, Literal

import aiohttp
import requests
import os
from dotenv import load_dotenv

from core.custom_exceptions.general_exceptions import NotifyDatabaseOfSalesFailedException

load_dotenv()
APP_SHEET_ACCESS_KEY = os.environ["APPSHEETACCESSKEY"]
DB_URL = os.environ["DBURL"]
ORM_USERID = os.environ["ORMUSERID"]
ORM_ACCESSKEY = os.environ["ORMACCESSKEY"]
URL = str


class SaleData:
    sku: str
    quantity: int

    def __init__(self, sku: str, quantity: int):
        self.sku = sku
        self.quantity = quantity

    def __repr__(self):
        return f"SaleData(sku={self.sku}, quantity={self.quantity})"


class Sales:
    sales: List[SaleData]

    def __init__(self):
        self.sales = []
        self.db_url = DB_URL

    def add_order_to_sales(self, formatted_orders):
        for formatted_order in formatted_orders:
            if self.contains_sku(formatted_order["sku"]):
                self.increment_quantity(formatted_order["sku"], int(formatted_order["quantity"]))
            else:
                self.sales.append(SaleData(sku=formatted_order["sku"], quantity=int(formatted_order["quantity"])))

    def increment_quantity(self, sku: str, quantity: int):
        for sale in self.sales:
            if sale.sku == sku:
                sale.quantity += quantity

    def contains_sku(self, sku: str) -> bool:
        for sale in self.sales:
            if sale.sku == sku:
                return True
        return False

    def notify_database_of_sales(self):
        # Depreciated. Moved to notify-sales endpoint of marketUpdateService
        return
        if len(self.sales) == 0:
            print("No sales to notify database of")
            return

        headers = {
            "user-id": ORM_USERID,
            "auth-key": ORM_ACCESSKEY
        }
        payload = {
            "sales": [
                {
                    "sku": sale.sku,
                    "quantity": sale.quantity
                }
                for sale in self.sales]
        }
        print(f"Sending payload: {payload} to {self.db_url} with headers: {headers}")
        resp = requests.post(
            url=self.db_url,
            headers=headers,
            json=payload
        )

        if resp.status_code != 200:
            raise NotifyDatabaseOfSalesFailedException(f"Failed to notify database of sales. "
                                                       f"Reason {resp.reason},"
                                                       f" JSON: {resp.json()}")
        print(f"Successfully notified database of sales")


def updateAppSheetWithRows(rows: List):
    return
    resp = requests.post(
        url='https://api.appsheet.com/api/v2/apps/6aec3910-fe2b-4d41-840e-aee105698fe3/tables/Order_Notice/Add',
        headers={'Content-Type': 'application/json',
                 'applicationAccessKey': APP_SHEET_ACCESS_KEY},
        data=json.dumps({
            "Action": "Add",
            "Properties": {
                "Locale": "en-US",
                "Location": "47.623098, -122.330184",
                "Timezone": "Pacific Standard Time",
                "UserSettings": {
                    "Option 1": "value1",
                    "Option 2": "value2"
                }
            },
            "Rows": rows
        }))
    if resp.status_code == 200:
        print(f"Updated sheet! with {rows}. Response code {resp.status_code}")
    else:
        print(f"Update sheet failed! Code: {resp.status_code} message: {resp.reason}")


# def getShipperName(price: float, chosenShipperName: str, country_code: str, remoteCheckCode):
#     # last condition in the IF is to filter out any shippers such as UPS Express or DHL Express
#     if price < 800 and remoteCheckCode == 204 and len(chosenShipperName.split(" ")) == 1 and \
#             country_code not in ("ES", "SE"):
#         return "ups"
#     else:
#         return "dhlexpress"


def getShipperName(price: float, chosenShipperName: str, country_code: str):
    # last condition in the IF is to filter out any shippers such as UPS Express or DHL Express
    if price < 800 and len(chosenShipperName.split(" ")) == 1 and \
            country_code not in ("ES", "SE"):
        return "ups"
    else:
        return "dhlexpress"


def getCurrentPriceOfSku(sku, skuMap, vendor: Literal["BM", "RF"]):
    return skuMap[sku][vendor][sku[-2:]]


async def get_results_from_urls(urls: List[URL]) -> List:
    results = []
    async with aiohttp.ClientSession() as session:
        tasks = [session.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        for response in responses:
            results.append(await response.json())

    return results
