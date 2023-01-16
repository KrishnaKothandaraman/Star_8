import datetime
import json
from typing import Optional, List

import requests
import core.types.refurbedAPI as RFtypes
from core.custom_exceptions.general_exceptions import GenericAPIException
from core.marketplace_clients.clientinterface import MarketPlaceClient
from keys import keys


class RefurbedClient(MarketPlaceClient):
    key: str
    vendor: str

    def __init__(self, key: str):
        super().__init__(key)
        self.vendor = "Refurbed"
        self.dateFieldName = RFtypes.RFDateFieldName
        self.dateStringFormat = RFtypes.RFDateStringFormat
        self.itemKeyName = RFtypes.RFItemKeyName
        self.skuFieldName = RFtypes.RFSKUFieldName
        self.orderIDFieldName = RFtypes.RFOrderIDFieldName

    def __getAuthHeader(self):
        return {"Authorization": self.key}

    def __crawlURL(self, url, payload):
        orders = []
        while True:
            print(f"Making Request")

            resp = requests.post(url=url,
                                 headers=self.__getAuthHeader(), data=json.dumps(payload))
            if resp.status_code != 200:
                print(f"Error occured {resp.status_code}")
                raise GenericAPIException(resp.reason)

            resp_json = resp.json()
            orders += resp_json["orders"]
            if resp_json["has_more"]:
                starting_after = resp_json['orders'][-1]['id']
                payload["pagination"] = {"starting_after": str(starting_after)}
            else:
                break

        return orders

    def getOrdersBetweenDates(self, start: datetime.datetime, end: datetime.datetime):
        """
        :param start: ISO 8601 format date string
        :param end: ISO 8601 format date string
        :return: response
        """
        start = self.convertDateTimeToString(start, "T00:00:00.00000Z")
        end = self.convertDateTimeToString(end, "T23:59:59.9999Z")

        print(start, end)
        print(f"INFO: Sending request to RF")
        payload = {
            "filter": {
                "released_at": {
                    "ge": start,
                    "le": end
                }
            },
        }
        orders = self.__crawlURL(url="https://api.refurbed.com/refb.merchant.v1.OrderService/ListOrders",
                                 payload=payload)

        print(f"Refurbed {len(orders)}")
        return orders

    def getOrderByID(self, orderID):
        print(f"INFO: Sending request to RF")

        resp = requests.post(url="https://api.refurbed.com/refb.merchant.v1.OrderService/ListOrders",
                             headers=self.__getAuthHeader(), data=json.dumps({"id": str(orderID)}))

        if resp.status_code != 200:
            raise GenericAPIException(resp.reason)

        return resp.json()

    def getOrdersByState(self, state: RFtypes.OrderStates):

        print(f"INFO: Sending request to BM for {state=}")
        url = f"https://api.refurbed.com/refb.merchant.v1.OrderService/ListOrders"
        payload = {
            "filter": {
                "state": {
                    "any_of": [
                        state
                    ]
                }
            }
        }

        return self.__crawlURL(url=url, payload=payload)

    def updateOrderStateByOrderID(self, orderID: str, sku: str, newState: int) -> requests.Response:

        print(f"RF: Updating state of {orderID} and sku {sku}")
        url = f"https://api.refurbed.com/refb.merchant.v1.OrderItemService/UpdateOrderItemState"
        body = {
            "order_id": int(orderID),
            "new_state": newState,
            "sku": sku
        }
        print(f"Sending {body=}")
        resp = requests.post(url=url,
                             headers=self.__getAuthHeader(),
                             data=body)
        return resp

    @staticmethod
    def generateItemsBodyForSWDCreateOrderRequest(orderItems: List[dict], swdModelName: str) -> List[dict]:
        items = []
        for orderItem in orderItems:
            listing = orderItem["listing"]
            quantity = orderItem["quantity"]
            price = orderItem["price"]
            productItem = {
                "skuType": "reference",
                "sku": listing,
                "amount": quantity,
                "price": price
            }
            adapterItem = [{
                "skuType": "reference",
                "sku": "002204",
                "amount": quantity,
                "price": 2
            }]
            if "EUS" in swdModelName and any(substr in swdModelName for substr in ("iPad 9", "iPad 8")):
                adapterItem = [{
                    "skuType": "reference",
                    "sku": "002479",
                    "amount": quantity,
                    "price": 2
                }]
            elif "EUS" in swdModelName and "iPad 7" in swdModelName:
                adapterItem = [{
                    "skuType": "reference",
                    "sku": "002351",
                    "amount": quantity,
                    "price": 2
                }]
            elif "EUS" in swdModelName and any(
                    substr in swdModelName for substr in ("iPad Pro", "iPad Air 4th", "iPad Air 5th")):
                adapterItem = [{
                    "skuType": "reference",
                    "sku": "002478",
                    "amount": quantity,
                    "price": 2
                }]
            elif "EUS" in swdModelName and any(
                    substr in swdModelName for substr in ("iPhone 12", "iPhone 13", "iPhone 14")):
                adapterItem = [
                    {
                        "skuType": "reference",
                        "sku": "002331",
                        "amount": quantity,
                        "price": 2
                    },
                ]
            elif "EUS" in swdModelName and any(
                    substr in swdModelName for substr in ("iPhone 11", "iPhone XR")):
                adapterItem = [
                    {
                        "skuType": "reference",
                        "sku": "002331",
                        "amount": quantity,
                        "price": 2
                    },
                    {
                        "skuType": "barcode",
                        "sku": "002510",
                        "amount": quantity,
                        "price": 2
                    }
                ]
            elif "EUS" not in swdModelName:
                adapterItem = None

            items.append(productItem)
            if adapterItem:
                items += adapterItem
        return items



# rf = RefurbedClient(key=keys["RF"]["token"])
# print(rf.getOrdersByState("ACCEPTED")[0])
