import datetime
import enum
import json
import requests
from pandas import to_datetime as to_datetime
from core.custom_exceptions.general_exceptions import GenericAPIException
from core.marketplace_clients.clientinterface import MarketPlaceClient


class BackMarketOrderStates(enum.Enum):
    New: 0
    Pending_Payment: 10
    Accept: 1
    Pending_Shipment: 3
    Payment_Failed: 8
    Shipped: 9

    @staticmethod
    def getStrFromEnum(val):
        return {
            0: "NEW", 10: "PENDING PAYMENT", 1: "ACCEPTED", 3: "PENDING SHIPMENT", 8: "PAYMENT FAILED", 9: "SHIPPED"
        }[val]


class BackMarketGender(enum.Enum):
    Male: 0
    Female: 1

    @staticmethod
    def getStrFromEnum(val):
        return {
            0: "MALE", 1: "FEMALE"}[val]


class BackMarketOrderlinesStates(enum.Enum):
    New: 0
    Validate_Orderline: 1
    Order_Accepted: 2
    Shipped: 3
    Cancelled: 4
    Refund_Before_Shipping: 5
    Refund_After_Shipping: 6
    Payment_Failed: 7
    Awaiting_Payment: 8

    @staticmethod
    def getStrFromEnum(val):
        return {
            0: "NEW", 1: "VALIDATE ORDERLINE", 2: "ORDER ACCEPTED", 3: "SHIPPED", 4: "CANCELLED",
            5: "REFUND BEFORE SHIPPING", 6: "REFUND AFTER SHIPPING", 7: "PAYMENT FAILED", 8: "AWAITING PAYMENT"
        }[val]


class BackMarketClient(MarketPlaceClient):

    def __init__(self, key: str, dateFieldName: str, dateStringFormat: str, itemKeyName: str):
        super().__init__(key)
        self.vendor = "BackMarket"
        self.dateFieldName = dateFieldName
        self.dateStringFormat = dateStringFormat
        self.itemKeyName = itemKeyName

    def getOrdersBetweenDates(self, start: datetime.datetime, end: datetime.datetime):

        start = self.convertDateTimeToString(start, " 00:00:00")
        end = self.convertDateTimeToString(end, " 23:59:59")

        print(f"INFO: Sending request to BM")
        nextURL = f"https://www.backmarket.fr/ws/orders?date_creation={start}"
        numOrders = 0
        orders = []

        while nextURL:
            print(f"Making call to {nextURL}")
            resp = requests.get(url=nextURL,
                                headers={"Authorization": f"basic {self.key}"})
            if resp.status_code != 200:
                print(f"Error occured {resp.status_code}")
                raise GenericAPIException(resp.reason)

            nextURL = resp.json()["next"]
            results = resp.json()["results"]
            numOrders += len(results)
            for res in results:
                res["state"] = BackMarketOrderStates.getStrFromEnum(val=int(res["state"]))
                res["shipping_address"]["gender"] = BackMarketGender.getStrFromEnum(val=int(res["shipping_address"]["gender"]))
                res["billing_address"]["gender"] = BackMarketGender.getStrFromEnum(val=int(res["billing_address"]["gender"]))
                for order in res["orderlines"]:
                    order["state"] = BackMarketOrderlinesStates.getStrFromEnum(val=int(order["state"]))
            orders += [res for res in results if
                       to_datetime(res["date_creation"]).strftime("%Y-%m-%d %H:%M:%S") <= end]

        print(f"Back Market: {numOrders=}")
        return orders

    def getSpecificOrder(self, orderID):
        print(f"INFO: Sending request to BM")
        url = f"https://www.backmarket.fr/ws/orders/{orderID}"

        resp = requests.get(url=url, headers={"Authorization": f"basic {self.key}"})

        if resp.status_code != 200:
            raise GenericAPIException(resp.reason)

        return resp.json()


if __name__ == "__main__":
    c = BackMarketClient(key="YmFjazJsaWZlcHJvZHVjdHNAb3V0bG9vay5jb206ODMyNzhydWV3ZmI3MzpmbmopKE52OCY4", itemKeyName="orderlines", dateFieldName="date_creation", dateStringFormat="%Y-%m-%dT%H:%M:%S%z")
    with open("data/bm/orders/2023-01-03/2023-01-03.json") as f:
        order = json.load(f)
    converted = (c.convertOrdersToSheetColumns([order]))
    for con in converted:
        print(con)
