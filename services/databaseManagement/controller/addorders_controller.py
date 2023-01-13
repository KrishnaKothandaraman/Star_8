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


def updateAppSheetWithRows(rows: List):
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
                "sku": sku}
    stockCheckResp = requests.post(url="https://admin.shopwedo.com/api/getStock", data=formData)

    if stockCheckResp.status_code != 200:
        raise GenericAPIException

    for obj in stockCheckResp.json():
        if obj["reference2"] == sku and obj["atp"] > 0:
            return True, obj["description"], obj["atp"]

    return False, "", ""


def performSWDAddOrder():
    bmClient = BackMarketClient(key=keys["BM"]["token"])

    newOrders = bmClient.getOrdersByState(state=1)

    for order in newOrders:
        country = order["shipping_address"]["country"]
        postal_code = order["shipping_address"]["postal_code"]
        courier_code = order["shipper"].split(" ")[0]
        orderItems = bmClient.getOrderItems(order)
        remoteCheckCode = performRemoteCheck(country, postal_code, courier_code)

        for orderline in orderItems:
            listing = bmClient.getSku(orderline)
            stockExists, swdModelName, stockAmount = performSWDStockCheck(listing)

            if not stockExists:
                updateAppSheetWithRows(rows=[{"order_id": bmClient.getOrderID(order),
                                              "Note": f"This Over _sell  {listing}  need ask the Buyer change to "
                                                      f"other: / some Stock waiting Book in / "
                                              }]
                                       )
                break
        # else here means the inner loop was excited normally. No break
        else:
            pass


# performSWDAddOrder()
