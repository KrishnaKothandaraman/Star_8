import enum
import requests
from pandas import to_datetime as to_datetime
from core.custom_exceptions.general_exceptions import GenericAPIException


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

class BackMarketClient:
    key: str

    def __init__(self, key):
        self.key = key

    def getOrdersBetweenDates(self, start, end):

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
