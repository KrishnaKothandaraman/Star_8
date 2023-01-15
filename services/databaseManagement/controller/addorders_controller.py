import hashlib
import hmac
import json
import random
import string
import time
import requests
from typing import Tuple, List
from core.custom_exceptions.general_exceptions import GenericAPIException
from core.marketplace_clients.bmclient import BackMarketClient
from core.marketplace_clients.clientinterface import MarketPlaceClient
from keys import keys


# utility function for swd authentication
def generateSalt() -> str:
    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(128 // 8))


# utility function for swd authentication
def generateHash(timestamp, salt) -> str:
    return hmac.new(
        msg=f"{keys['shopwedo']['shopid']}{keys['shopwedo']['shopkey']}{timestamp}{salt}".encode(),
        key=keys['shopwedo']['shopkey'].encode(), digestmod=hashlib.sha512).hexdigest()


# utility for swd auth
def generateSWDAuthJson():
    timestamp = int(time.time())
    salt = generateSalt()
    token = generateHash(timestamp=timestamp, salt=salt)
    return {
        "shopid": keys['shopwedo']['shopid'],
        "timestamp": timestamp,
        "salt": salt,
        "token": token
    }


def getSWDCreateOrderBody(formattedOrder: dict, items: []):
    """Returns body for swd create order request from formatted order"""
    return {
        "external_order_id": str(formattedOrder["order_id"]),
        "external_order_reference": str(formattedOrder["order_id"]),
        "release": "y",
        "shipping_method": "ship",
        "shipping_company": formattedOrder["shipper"],
        "shipping_address": {
            "firstname": formattedOrder["shipping_first_name"],
            "lastname": formattedOrder["shipping_last_name"],
            "company": formattedOrder["company"],
            "street": f"{formattedOrder['shipping_address1']},{formattedOrder['shipping_address1']}",
            "box": "",
            "zip": formattedOrder["shipping_postal_code"],
            "city": formattedOrder["shipping_city"],
            "country_iso2": formattedOrder["shipping_country_code"],
            "phone": formattedOrder["shipping_phone_number"],
            "email": formattedOrder["customer_email"]
        },
        "items": items
    }


def updateAppSheetWithRows(rows: List):
    print(f"Updated sheet! with {rows}")
    return
    requests.post(
        url='https://api.appsheet.com/api/v2/apps/6aec3910-fe2b-4d41-840e-aee105698fe3/tables/Order_Notice/Add',
        headers={'Content-Type': 'application/json',
                 'applicationAccessKey': keys["appsheet_accesskey"]},
        data={
            "mode": 'raw',
            "raw": {
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
            }
        })


def performRemoteCheck(country: str, postal_code: str, shipper: str) -> int:
    headers = {"Tracking-Api-Key": keys["remote-check"]}
    body = {
        "country": f"{country}",
        "postal_code": f"{postal_code}",
        "courier_code": f"{shipper}"
    }
    remoteCheckResp = requests.post(url="https://api.trackingmore.com/v3/trackings/remote", headers=headers,
                                    data=json.dumps(body))
    if remoteCheckResp.status_code != 200:
        raise GenericAPIException("Remote check failed")

    return remoteCheckResp.json()["code"]


def performSWDStockCheck(sku: str) -> Tuple[bool, str, str]:
    formData = {"auth": json.dumps(generateSWDAuthJson()),
                "data": json.dumps({"reference": sku})}
    stockCheckResp = requests.post(url="https://admin.shopwedo.com/api/getStock", data=formData)

    if stockCheckResp.status_code != 200:
        raise GenericAPIException
    # loop through response and check master_atp field which is stock for this listing
    for listing, data in stockCheckResp.json().items():
        if data["reference2"] == sku:
            if int(data["master_atp"]) > 0:
                return True, data["description"], data["master_atp"]
            else:
                break

    return False, "", ""


def performSWDCreateOrder(formattedOrder, items) -> requests.Response:
    formData = {"auth": json.dumps(generateSWDAuthJson()),
                "data": json.dumps(getSWDCreateOrderBody(formattedOrder, items))}
    createOrderResponse = requests.post(url="https://admin.shopwedo.com/api/createOrder", data=formData)
    return createOrderResponse


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
        adapterItem = {
            "skuType": "reference",
            "sku": "002204",
            "amount": quantity,
            "price": 2
        }
        if "EUS" in swdModelName and any(substr in swdModelName for substr in ("iPad 9", "iPad 8")):
            adapterItem = {
                "skuType": "reference",
                "sku": "002479",
                "amount": quantity,
                "price": 2
            }
        elif "EUS" in swdModelName and "iPad 7" in swdModelName:
            adapterItem = {
                "skuType": "reference",
                "sku": "002351",
                "amount": quantity,
                "price": 2
            }
        elif "EUS" in swdModelName and any(
                substr in swdModelName for substr in ("iPad Pro", "iPad Air 4th", "iPad Air 5th")):
            adapterItem = {
                "skuType": "reference",
                "sku": "002478",
                "amount": quantity,
                "price": 2
            }
        elif "EUS" in swdModelName and any(
                substr in swdModelName for substr in ("iPhone 12", "iPhone 13", "iPhone 14")):
            adapterItem = {
                "skuType": "reference",
                "sku": "002331",
                "amount": quantity,
                "price": 2
            }
        elif "EUS" not in swdModelName:
            adapterItem = None

        items.append(productItem)
        if adapterItem:
            items.append(adapterItem)
    return items


def processNewOrders(orders: List, MarketClient: MarketPlaceClient) -> int:
    """
    Performs logic to loop through orders and create SWD orders if stock exists
    :param orders: List of orders
    :param MarketClient: Marketplace that the orders are from
    :return:
    """
    updateCounter = 0
    for order in orders:
        formattedOrder = MarketClient.convertOrderToSheetColumns(order)
        remoteCheckCode = performRemoteCheck(formattedOrder["shipping_country_code"],
                                             formattedOrder["shipping_postal_code"],
                                             formattedOrder["shipper"].split(" ")[0])
        orderItems = MarketClient.getOrderItems(order)
        stockExists, swdModelName, stockAmount = "", "", ""
        # last condition in the IF is to filter out any shippers such as UPS Express or DHL Express
        if float(formattedOrder["total_charged"]) < 800 and remoteCheckCode == 204 \
                and len(formattedOrder["shipper"].split(" ")) == 1 and formattedOrder["shipping_country_code"] != "ES":
            formattedOrder["shipper"] = "ups"
        else:
            formattedOrder["shipper"] = "dhlexpress"

        print(
            f"For {formattedOrder['order_id']} to country {formattedOrder['shipping_country_code']}, set shipper to {formattedOrder['shipper']}")
        for orderline in orderItems:
            listing = MarketClient.getSku(orderline)
            stockExists, swdModelName, stockAmount = performSWDStockCheck(listing)
            if not stockExists:
                updateAppSheetWithRows(rows=[{"order_id": MarketClient.getOrderID(order),
                                              "Note": f"This Over _sell  {listing}  need ask the Buyer change to "
                                                      f"other: / some Stock waiting Book in / "
                                              }]
                                       )
                break

        # else here means the orderline loop was excited normally. No break
        else:
            print(f"All stock exists for order {swdModelName}")
            items = generateItemsBodyForSWDCreateOrderRequest(orderItems, swdModelName)
            createOrderResp = performSWDCreateOrder(formattedOrder, items)
            if createOrderResp.status_code != 201:
                updateAppSheetWithRows(rows=[{"order_id": formattedOrder["order_id"],
                                              "Note": f"Shop we do add order failed. Error code: {createOrderResp.status_code}"
                                                      f",Error json {createOrderResp.json()}"
                                              }]
                                       )
            else:
                errors = 0
                for orderline in orderItems:
                    sku: str = MarketClient.getSku(orderline)
                    resp = MarketClient.updateOrderStateByOrderID(str(formattedOrder["order_id"]), sku, 2)
                    if resp.status_code != 200:
                        print(f"ERROR for {formattedOrder['order_id']} {sku}. "
                              f"Manully check in. Updated Failed: Code: {resp.status_code}, Resp: {resp.json()}")
                        errors += 1
                    else:
                        updateCounter += 1
                        print(f"Updated state of {formattedOrder['order_id']} to {2}. Return code {resp.status_code}")
                if errors:
                    raise GenericAPIException
    return updateCounter

def performSWDAddOrder():
    """Call this method to run the workflow to pull new orders and add orders to SWD"""
    bmClient = BackMarketClient(key=keys["BM"]["token"])

    newOrders = bmClient.getOrdersByState(state=1)

    return processNewOrders(newOrders, bmClient)

# performSWDAddOrder()
