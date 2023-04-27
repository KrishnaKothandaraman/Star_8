import datetime
import json
import os
from typing import Optional, List, Dict, Tuple
import aiohttp
import requests
from dotenv import load_dotenv
import core.types.refurbedAPI as RFtypes
from core.custom_exceptions.general_exceptions import GenericAPIException
from core.marketplace_clients.clientinterface import MarketPlaceClient

from core.types.orderStateTypes import newStates
from services.database_management.app.controller.utils.swd_utils import SWDShippingData

load_dotenv()
RF_ACCESS_KEY = os.environ["RFTOKEN"]


class RefurbedClient(MarketPlaceClient):
    key: str
    vendor: str
    URL_PREFIX: str = "https://api.refurbed.com/refb.merchant.v1."
    ORDERSERVICE_URL_PREFIX: str = URL_PREFIX + "OrderService"
    ITEMSERVICE_URL_PREFIX: str = URL_PREFIX + "OrderItemService"
    OFFERSERVICE_URL_PREFIX: str = URL_PREFIX + "OfferService"
    MARKET_OFFERSERVICE_URL_PREFIX: str = URL_PREFIX + "MarketOfferService"

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
        for swd_model_name, order_item in list(zip(swdModelNames, orderItems)):
            listing = order_item["sku"]
            quantity = 1
            price = order_item["settlement_total_charged"]
            item_id = order_item["id"]
            product_item = {
                "external_orderline_id": item_id,
                "skuType": "reference",
                "sku": listing,
                "amount": quantity,
                "price": price
            }
            adapter_item = [{
                "skuType": "reference",
                "sku": "002204",
                "amount": quantity,
                "price": 2
            }]
            if "EUS" in swd_model_name and any(substr in swd_model_name for substr in ("iPad 9", "iPad 8")):
                adapter_item = [{
                    "skuType": "reference",
                    "sku": "002479",
                    "amount": quantity,
                    "price": 2
                }]
            elif "EUS" in swd_model_name and "iPad 7" in swd_model_name:
                adapter_item = [{
                    "skuType": "reference",
                    "sku": "002351",
                    "amount": quantity,
                    "price": 2
                }]
            elif "EUS" in swd_model_name and "Samsung" in swd_model_name:
                adapter_item = [{
                    "skuType": "reference",
                    "sku": "002694",
                    "amount": quantity,
                    "price": 2
                }]
            elif "EUS" in swd_model_name and any(
                    substr in swd_model_name for substr in ("iPad Pro", "iPad Air 4th", "iPad Air 5th")):
                adapter_item = [{
                    "skuType": "reference",
                    "sku": "002478",
                    "amount": quantity,
                    "price": 2
                }]
            elif "EUS" in swd_model_name and any(
                    substr in swd_model_name for substr in ("iPhone 12", "iPhone 13", "iPhone 14")):
                adapter_item = [
                    {
                        "skuType": "reference",
                        "sku": "002331",
                        "amount": quantity,
                        "price": 2
                    },
                ]
            elif "EUS" in swd_model_name and any(
                    substr in swd_model_name for substr in ("iPhone 11", "iPhone XR")):
                adapter_item = [
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
            elif "EUS" not in swd_model_name:
                adapter_item = None

            items.append(product_item)
            if adapter_item:
                items += adapter_item
        return items

    # @staticmethod
    # def getBodyForUpdateStateToShippedRequest(order, swdRespBody: dict, item: dict) -> dict:
    #     trackingData = {"id": order["item_id"],
    #                     "state": "SHIPPED",
    #                     "parcel_tracking_url": swdRespBody["shipping"][0]["tracking_url"],
    #                     "item_identifier": item["serialnumber"][0]}
    #
    #     return trackingData

    @staticmethod
    def getBodyForUpdateStateToShippedRequest(shipping_data: SWDShippingData) -> dict:
        tracking_data = {"id": shipping_data.item_id,
                         "state": "SHIPPED",
                         "parcel_tracking_url": shipping_data.tracking_url,
                         "item_identifier": shipping_data.serial_number
                         }

        # if shipping_data.is_multi_sku:
        #     del trackingData["item_identifier"]

        return tracking_data

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

    def __crawlURL(self, url, payload, keyName: str):
        orders = []
        while True:
            print("Making Request")

            resp = requests.post(url=url,
                                 headers=self.__getAuthHeader(), data=json.dumps(payload))
            if resp.status_code != 200:
                print(f"Error occured {resp.status_code}")
                raise GenericAPIException(resp.reason)

            resp_json = resp.json()
            orders += resp_json[keyName]
            if resp_json["has_more"]:
                starting_after = resp_json[keyName][-1]['id']
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
        print("INFO: Sending request to RF")
        payload = {
            "filter": {
                "released_at": {
                    "ge": start,
                    "le": end
                }
            },
        }
        orders = self.__crawlURL(url=f"{self.ORDERSERVICE_URL_PREFIX}/ListOrders",
                                 payload=payload, keyName="orders")

        print(f"Refurbed: {len(orders)}")
        return orders

    def getOrderByID(self, orderID, normalizeFields=None):
        print("INFO: Sending request to RF")
        payload = {
            "id": str(orderID)
        }
        resp = requests.post(url=f"{self.ORDERSERVICE_URL_PREFIX}/GetOrder",
                             headers=self.__getAuthHeader(), data=json.dumps(payload))

        if resp.status_code != 200:
            raise GenericAPIException(resp.reason)
        return resp.json()["order"]

    def getOrdersByState(self, state: RFtypes.OrderStates):

        print(f"INFO: Sending request to RF for {state=}")
        url = f"{self.ORDERSERVICE_URL_PREFIX}/ListOrders"
        payload = {
            "filter": {
                "state": {
                    "any_of": [
                        state
                    ]
                }
            }
        }

        orders = self.__crawlURL(url=url, payload=payload, keyName="orders")

        print(f"Refurbed: {len(orders)}")

        return orders

    def updateStateOfOrder(self, order, state: newStates, body):
        errors = 0
        update_counter = 0
        new_state = self.__getMarketPlaceState(state)
        for orderline in order[self.itemKeyName]:
            order_id = str(self.getOrderID(order))
            # Accept by item_id
            item_id = orderline["id"]
            body = self.__getBodyForUpdateRequestByState(order=order,
                                                         orderline=orderline,
                                                         state=new_state) if not body else body
            resp = self.MakeUpdateOrderStateByOrderIDRequest(orderID=str(order_id),
                                                             body=body)
            body = None
            if resp.status_code != 200:
                print(f"ERROR for {order_id} {item_id}. "
                      f"Manully check in. Updated Failed: Code: {resp.status_code}"
                      f", Reason: {resp.reason}")
                errors += 1
            else:
                update_counter += 1
                print(f"Updated state of {order_id}, {item_id} to {new_state}."
                      f"Return code {resp.status_code}")

        if errors:
            raise GenericAPIException("Update state to RF had errors")

        return update_counter

    def MakeUpdateOrderStateByOrderIDRequest(self, orderID, body) -> requests.Response:

        print(f"RF: Updating state of {orderID}")
        url = f"{self.ITEMSERVICE_URL_PREFIX}/UpdateOrderItemState"
        print(f"Sending {body=}")
        resp = requests.post(url=url,
                             headers=self.__getAuthHeader(),
                             data=json.dumps(body))
        return resp

    async def getListing(self, listingFilter: Tuple[str, str], clientSession: aiohttp.ClientSession):
        print(f"Getting listing from RF")
        url = f"{self.OFFERSERVICE_URL_PREFIX}/GetOffer"

        payload = {
            "identifier": {
                listingFilter[0]: str(listingFilter[1])
            },
        }
        resp = clientSession.post(url=url,
                                  headers=self.__getAuthHeader(),
                                  data=json.dumps(payload))
        print("RF done")
        return await resp

    def update_market_offer(self, sku: str, updates: List[Tuple]):
        print(f"Updating RF Listing for {sku}")
        url = f"{self.MARKET_OFFERSERVICE_URL_PREFIX}/UpdateOffer"
        payload = {
            "identifier": {
                "sku": sku
            },
        }
        for update in updates:
            payload[update[0]] = update[1]

        print(f"Sending payload {payload}")
        resp = requests.post(url=url,
                             headers=self.__getAuthHeader(),
                             data=json.dumps(payload))
        return resp

    def get_list_of_all_offers(self):
        """
        Method to get all offers from Refurbed
        :return: List of offers
        """
        url = f"{self.OFFERSERVICE_URL_PREFIX}/ListOffers"
        payload = {}
        offers = self.__crawlURL(url=url, payload=payload, keyName="offers")
        return offers

    # rf = RefurbedClient()
# with open("offers.json", "r") as f:
#     # print length of offers
#     print(len(json.load(f)))
