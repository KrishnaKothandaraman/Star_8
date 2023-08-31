import datetime
import json
from typing import Optional, List, Tuple, Dict
import aiohttp
import requests
import core.types.backmarketAPI as BMTypes
from pandas import to_datetime as to_datetime
from core.custom_exceptions.general_exceptions import GenericAPIException
from core.marketplace_clients.clientinterface import MarketPlaceClient
import os
from dotenv import load_dotenv
from core.types.orderStateTypes import newStates
from services.database_management.app.controller.utils.swd_utils import SWDShippingData

load_dotenv()
BM_KEY = os.environ["BMTOKEN"]


class BackMarketClient(MarketPlaceClient):

    def __init__(self):
        super().__init__()
        self.key = BM_KEY
        self.vendor = "BackMarket"
        self.dateFieldName = BMTypes.BMDateFieldName
        self.dateStringFormat = BMTypes.BMDateStringFormat
        self.itemKeyName = BMTypes.BMItemKeyName
        self.skuFieldName = BMTypes.BMSKUFieldName
        self.orderIDFieldName = BMTypes.BMOrderIDFieldName

    @staticmethod
    def generateItemsBodyForSWDCreateOrderRequest(orderItems: List[dict], swdModelNames: List[str]) -> List[dict]:
        items = []
        swdModelNames = list(map(lambda x: x.lower(), swdModelNames))

        for swdModelName, orderItem in list(zip(swdModelNames, orderItems)):
            listing = orderItem["listing"]
            quantity = orderItem["quantity"]
            price = orderItem["price"]
            item_id = orderItem["id"]
            productItem = {
                "external_orderline_id": item_id,
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
            if "eus" in swdModelName and any(
                    substr.lower() in swdModelName for substr in ("iPad 9", "iPad 8")):
                adapterItem = [{
                    "skuType": "reference",
                    "sku": "002479",
                    "amount": quantity,
                    "price": 2
                }]
            elif "eus" in swdModelName and any(substr.lower() in swdModelName for substr in ("iPad 7", "iPad 6")):
                adapterItem = [{
                    "skuType": "reference",
                    "sku": "002479",
                    "amount": quantity,
                    "price": 2
                }]
            elif "eus" in swdModelName and any(
                    substr.lower() in swdModelName for substr in ("iPad Pro", "iPad Air 4th", "iPad Air 5th", "iPad 10")):
                adapterItem = [{
                    "skuType": "reference",
                    "sku": "002478",
                    "amount": quantity,
                    "price": 2
                }]
            elif "eus" in swdModelName and "samsung" in swdModelName:
                adapterItem = [{
                    "skuType": "reference",
                    "sku": "002694",
                    "amount": quantity,
                    "price": 2
                }]
            elif "eus" in swdModelName and any(
                    substr.lower() in swdModelName for substr in ("iPhone 12", "iPhone 13", "iPhone 14")):
                adapterItem = [
                    {
                        "skuType": "reference",
                        "sku": "002331",
                        "amount": quantity,
                        "price": 2
                    },

                ]
                if not any(item["sku"] == "SKU_136666" for item in items):
                    adapterItem += [{
                        "skuType": "barcode",
                        "sku": "SKU_136666",
                        "amount": quantity,
                        "price": 2
                    }]
            elif "eus" in swdModelName:
                adapterItem = {
                    "skuType": "reference",
                    "sku": "002204",
                    "amount": quantity,
                    "price": 2
                },
            elif "eus" not in swdModelName:
                adapterItem = None

            items.append(productItem)
            if adapterItem:
                items += adapterItem
        return items

    @staticmethod
    def getBodyForUpdateStateToShippedRequest(shipping_data: SWDShippingData) -> dict:
        trackingData = {"order_id": shipping_data.order_id,
                        "sku": shipping_data.sku,
                        "new_state": 3,
                        "tracking_number": shipping_data.tracking_number,
                        "tracking_url": shipping_data.tracking_url,
                        "shipper": shipping_data.shipper}

        if not shipping_data.is_multi_sku:
            if len(shipping_data.serial_number) == 15:
                trackingData["imei"] = shipping_data.serial_number
            else:
                trackingData["serial_number"] = shipping_data.serial_number

        return trackingData

    def __getAuthHeader(self):
        return {"Authorization": f"Basic {self.key}"}

    @staticmethod
    def __getMarketPlaceState(state: newStates) -> int:
        if state == "NEW":
            return BMTypes.BackMarketOrderlinesStates.Order_Accepted.value
        elif state == "UPLOAD_TRACKING":
            return BMTypes.BackMarketOrderlinesStates.Shipped.value

    def __getBodyForUpdateRequestByState(self, order: list, orderline: list, state: int):
        if state == BMTypes.BackMarketOrderlinesStates.Order_Accepted.value:
            return {
                "order_id": int(self.getOrderID(order)),
                "new_state": state,
                "sku": self.getSku(orderline)
            }
        else:
            raise NotImplementedError

    @staticmethod
    def __normalize_fields(order) -> dict:
        order["state"] = BMTypes.BackMarketOrderStates.getStrFromEnum(val=int(order["state"]))
        order["shipping_address"]["gender"] = BMTypes.BackMarketGender.getStrFromEnum(
            val=int(order["shipping_address"]["gender"]))
        order["billing_address"]["gender"] = BMTypes.BackMarketGender.getStrFromEnum(
            val=int(order["billing_address"]["gender"]))
        for orderline in order["orderlines"]:
            orderline["state"] = BMTypes.BackMarketOrderlinesStates.getStrFromEnum(val=int(orderline["state"]))
        return order

    def __crawlURL(self, url, endDate: Optional[str]):
        data = []
        orderCounter = 0
        while url:
            print(f"Making call to {url}")
            resp = requests.get(url=url,
                                headers=self.__getAuthHeader())
            if resp.status_code != 200:
                print(f"Error occured {resp.status_code}")
                raise GenericAPIException(resp.reason)

            url = resp.json()["next"]
            results = resp.json()["results"]
            orderCounter += len(results)
            for res in results:
                res["state"] = BMTypes.BackMarketOrderStates.getStrFromEnum(val=int(res["state"]))
                res["shipping_address"]["gender"] = BMTypes.BackMarketGender.getStrFromEnum(
                    val=int(res["shipping_address"]["gender"]))
                res["billing_address"]["gender"] = BMTypes.BackMarketGender.getStrFromEnum(
                    val=int(res["billing_address"]["gender"]))
                for order in res["orderlines"]:
                    order["state"] = BMTypes.BackMarketOrderlinesStates.getStrFromEnum(val=int(order["state"]))

            oldLen = len(data)
            if not endDate:
                data += [res for res in results]
            else:
                data += [res for res in results if
                         (to_datetime(res["date_creation"]).strftime("%Y-%m-%d %H:%M:%S") <= endDate)]

            # all older orders
            if len(data) - oldLen == 0:
                print(f"Reached the stage of older orders. Breaking out")
                break

        print(f"Back Market: {orderCounter=}")
        return data

    def getOrdersBetweenDates(self, start: datetime.datetime, end: datetime.datetime):

        start = self.convertDateTimeToString(start, " 00:00:00")
        end = self.convertDateTimeToString(end, " 23:59:59")
        print(f"Filtering between {start} {end}")
        return self.__crawlURL(url=f"https://www.backmarket.fr/ws/orders?date_creation={start}", endDate=end)

    def getOrdersByLastModified(self, lastModifiedDate):

        start = self.convertDateTimeToString(lastModifiedDate, " 00:00:00")
        print(f"INFO: Sending request to BM")
        return self.__crawlURL(f"https://www.backmarket.fr/ws/orders?date_modification={start}", None)

    def getOrderByID(self, orderID, normalizeFields=None):
        print(f"INFO: Sending request to BM")
        url = f"https://www.backmarket.fr/ws/orders/{orderID}"

        resp = requests.get(url=url, headers=self.__getAuthHeader())

        if resp.status_code != 200:
            raise GenericAPIException(resp.reason)

        if not normalizeFields:
            return resp.json()
        else:
            return self.__normalize_fields(resp.json())

    def getOrdersByState(self, state):

        print(f"INFO: Sending request to BM for {state=}")
        url = f"https://www.backmarket.fr/ws/orders/?state={state}&page-size=50&page=1"

        return self.__crawlURL(url=url, endDate=None)

    def updateStateOfOrder(self, order, state: newStates, body):
        errors = 0
        updateCounter = 0
        newState = self.__getMarketPlaceState(state)
        for orderline in order[self.itemKeyName]:
            sku: str = self.getSku(orderline)
            order_id = self.getOrderID(order)
            body = self.__getBodyForUpdateRequestByState(order=order,
                                                         orderline=orderline,
                                                         state=newState) if not body else body
            resp = self.MakeUpdateOrderStateByOrderIDRequest(orderID=str(order_id),
                                                             body=body)
            body = None
            if resp.status_code != 200:
                print(f"ERROR for {order_id} {sku}. "
                      f"Manully check in. Updated Failed: Code: {resp.status_code}, Resp: {resp.json()}")
                errors += 1
            else:
                updateCounter += 1
                print(f"Updated state of {order_id} to {newState}. Return code {resp.status_code}")

        if errors:
            raise GenericAPIException(f"Update state to BM had errors")

        return updateCounter

    def MakeUpdateOrderStateByOrderIDRequest(self, orderID, body) -> requests.Response:

        print(f"BM: Updating state of {orderID}")
        url = f"https://www.backmarket.fr/ws/orders/{orderID}"

        print(f"Sending {body=}")
        resp = requests.post(url=url,
                             headers=self.__getAuthHeader(),
                             data=body)
        return resp

    async def getListing(self, listingFilter: Tuple[str, str], clientSession: aiohttp.ClientSession):
        print(f"Getting listing with {listingFilter}")

        url = f"https://www.backmarket.fr/ws/listings/detail?{listingFilter[0]}={listingFilter[1]}"
        resp = clientSession.get(url=url,
                                 headers=self.__getAuthHeader())
        print("BM Done!")
        return await resp

# async def test_listing(sku):
#     bm = BackMarketClient()
#     async with aiohttp.ClientSession() as clientSes:
#         resp = await bm.getListing(sku, clientSes)
#         print(await resp.json())
#
# if __name__ == "__main__":
#     bm = BackMarketClient()
#     #     # with open("dump.json", "w") as f:
#     #     #     f.write(
#     #     #         json.dumps(bm.getOrdersByState(state=1), indent=3))
#     #
#     #     # print(bm.getOrderByID("25923025"))
#     asyncio.run(test_listing(("listing_id", "2826949")))
