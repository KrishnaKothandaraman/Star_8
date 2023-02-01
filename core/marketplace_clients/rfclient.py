import datetime
import json
import os
import requests
import core.types.refurbedAPI as RFtypes
from typing import Optional, List
from core.custom_exceptions.general_exceptions import GenericAPIException
from core.marketplace_clients.clientinterface import MarketPlaceClient
from dotenv import load_dotenv

from core.types.orderStateTypes import newStates

load_dotenv()
RF_ACCESS_KEY = os.environ["RFTOKEN"]


class RefurbedClient(MarketPlaceClient):
    key: str
    vendor: str

    def __init__(self):
        super().__init__()
        self.key = RF_ACCESS_KEY
        self.vendor = "Refurbed"
        self.dateFieldName = RFtypes.RFDateFieldName
        self.dateStringFormat = RFtypes.RFDateStringFormat
        self.itemKeyName = RFtypes.RFItemKeyName
        self.skuFieldName = RFtypes.RFSKUFieldName
        self.orderIDFieldName = RFtypes.RFOrderIDFieldName

    @staticmethod
    def generateItemsBodyForSWDCreateOrderRequest(orderItems: List[dict], swdModelNames: List[str]) -> List[dict]:
        items = []
        for swdModelName, orderItem in list(zip(swdModelNames, orderItems)):
            listing = orderItem["sku"]
            quantity = 1
            price = orderItem["settlement_total_charged"]
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
                        "sku": "002204",
                        "amount": quantity,
                        "price": 2
                    },
                    # {
                    #     "skuType": "barcode",
                    #     "sku": "002510",
                    #     "amount": quantity,
                    #     "price": 2
                    # }
                ]
            elif "EUS" not in swdModelName:
                adapterItem = None

            items.append(productItem)
            if adapterItem:
                items += adapterItem
        return items

    @staticmethod
    def getBodyForUpdateStateToShippedRequest(order, swdRespBody: dict, item: dict) -> dict:
        trackingData = {"id": order["item_id"],
                        "state": "SHIPPED",
                        "parcel_tracking_url": swdRespBody["shipping"][0]["tracking_url"],
                        "item_identifier": item["serialnumber"][0]}

        return trackingData

    def __getAuthHeader(self):
        return {"Authorization": self.key}

    @staticmethod
    def __getMarketPlaceState(state: newStates) -> RFtypes.OrderStates:
        if state == "NEW":
            return "ACCEPTED"
        elif state == "UPLOAD_TRACKING":
            raise NotImplementedError

    def __getBodyForUpdateRequestByState(self, order, orderline, state):
        if state == "ACCEPTED":
            return {
                "id": orderline["id"],
                "state": state
            }

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

        print(f"Refurbed: {len(orders)}")
        return orders

    def getOrderByID(self, orderID):
        print(f"INFO: Sending request to RF")

        resp = requests.post(url="https://api.refurbed.com/refb.merchant.v1.OrderService/ListOrders",
                             headers=self.__getAuthHeader(), data=json.dumps({"id": str(orderID)}))

        if resp.status_code != 200:
            raise GenericAPIException(resp.reason)

        return resp.json()

    def getOrdersByState(self, state: RFtypes.OrderStates):

        print(f"INFO: Sending request to RF for {state=}")
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

        orders = self.__crawlURL(url=url, payload=payload)

        print(f"Refurbed: {len(orders)}")

        return orders

    def updateStateOfOrder(self, order, state: newStates, body):
        errors = 0
        updateCounter = 0
        newState = self.__getMarketPlaceState(state)
        for orderline in order[self.itemKeyName]:
            order_id = str(self.getOrderID(order))
            item_id = orderline["id"]
            body = self.__getBodyForUpdateRequestByState(order=order,
                                                         orderline=orderline,
                                                         state=newState) if not body else body
            resp = self.MakeUpdateOrderStateByOrderIDRequest(orderID=str(order_id),
                                                             body=body)
            if resp.status_code != 200:
                print(f"ERROR for {order_id} {item_id}. "
                      f"Manully check in. Updated Failed: Code: {resp.status_code}, Reason: {resp.reason}")
                errors += 1
            else:
                updateCounter += 1
                print(f"Updated state of {order_id}, {item_id} to {newState}. Return code {resp.status_code}")

        if errors:
            raise GenericAPIException(f"Update state to RF had errors")

        return updateCounter

    def MakeUpdateOrderStateByOrderIDRequest(self, orderID, body) -> requests.Response:

        print(f"RF: Updating state of {orderID}")
        url = f"https://api.refurbed.com/refb.merchant.v1.OrderItemService/UpdateOrderItemState"
        print(f"Sending {body=}")
        resp = requests.post(url=url,
                             headers=self.__getAuthHeader(),
                             data=json.dumps(body))
        return resp


# rf = RefurbedClient(key=keys["RF"]["token"])
# print(rf.updateStateOfOrder(rf.getOrdersByState("NEW")[0]))
