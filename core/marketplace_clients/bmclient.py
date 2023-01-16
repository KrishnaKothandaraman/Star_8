import datetime
from typing import Optional, List
import requests
import core.types.backmarketAPI as BMTypes
from pandas import to_datetime as to_datetime
from core.custom_exceptions.general_exceptions import GenericAPIException
from core.marketplace_clients.clientinterface import MarketPlaceClient


class BackMarketClient(MarketPlaceClient):

    def __init__(self, key: str):
        super().__init__(key)
        self.vendor = "BackMarket"
        self.dateFieldName = BMTypes.BMDateFieldName
        self.dateStringFormat = BMTypes.BMDateStringFormat
        self.itemKeyName = BMTypes.BMItemKeyName
        self.skuFieldName = BMTypes.BMSKUFieldName
        self.orderIDFieldName = BMTypes.BMOrderIDFieldName

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
                    {
                        "skuType": "barcode",
                        "sku": "SKU_136666",
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

    def __getAuthHeader(self):
        return {"Authorization": f"Basic {self.key}"}

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

    def getOrderByID(self, orderID):
        print(f"INFO: Sending request to BM")
        url = f"https://www.backmarket.fr/ws/orders/{orderID}"

        resp = requests.get(url=url, headers=self.__getAuthHeader())

        if resp.status_code != 200:
            raise GenericAPIException(resp.reason)

        return resp.json()

    def getOrdersByState(self, state):

        print(f"INFO: Sending request to BM for {state=}")
        url = f"https://www.backmarket.fr/ws/orders/?state={state}&page-size=50&page=1"

        return self.__crawlURL(url=url, endDate=None)

    def updateStateOfOrder(self, order):

        errors = 0
        updateCounter = 0
        for orderline in order[self.itemKeyName]:
            sku: str = self.getSku(orderline)
            order_id = self.getOrderID(order)
            resp = self.MakeUpdateOrderStateByOrderIDRequest(str(order_id), sku, 2)
            if resp.status_code != 200:
                print(f"ERROR for {order_id} {sku}. "
                      f"Manully check in. Updated Failed: Code: {resp.status_code}, Resp: {resp.json()}")
                errors += 1
            else:
                updateCounter += 1
                print(f"Updated state of {order_id} to {2}. Return code {resp.status_code}")

        if errors:
            raise GenericAPIException(f"Update state to BM had errors")

        return updateCounter

    def MakeUpdateOrderStateByOrderIDRequest(self, orderID: str, sku: str, newState: int) -> requests.Response:

        print(f"BM: Updating state of {orderID} and sku {sku}")
        url = f"https://www.backmarket.fr/ws/orders/{orderID}"
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


# if __name__ == "__main__":
#     bm = BackMarketClient(key="YmFjazJsaWZlcHJvZHVjdHNAb3V0bG9vay5jb206ODMyNzhydWV3ZmI3MzpmbmopKE52OCY4")
# #     # with open("dump.json", "w") as f:
# #     #     f.write(
# #     #         json.dumps(bm.getOrdersByState(state=1), indent=3))
# #
# #     # print(bm.getOrderByID("25923025"))
#     resp = bm.updateOrderStateByOrderID(orderID="25924512", sku="002029SH", newState=2)
#     print(resp.status_code)
#     print(resp.json())
#     print(resp.reason)
