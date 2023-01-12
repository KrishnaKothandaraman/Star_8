import hashlib
import hmac
import json
import random
import string
import time

import requests
from core.custom_exceptions.general_exceptions import GenericAPIException
from core.marketplace_clients.bmclient import BackMarketClient
from get_order_history import keys


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


def performSWDStockCheck(listing: str):
    formData = {"auth": json.dumps(generateSWDAuthJson()),
                "listing": listing}
    stockCheckResp = requests.post(url="https://admin.shopwedo.com/api/getStock", data=formData)

    print(stockCheckResp.status_code)
    print(stockCheckResp.json())
    return ""


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
            stockExists = performSWDStockCheck(listing)
            break
        break
performSWDAddOrder()