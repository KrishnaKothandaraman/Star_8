import hashlib
import hmac
import json
import random
import string
import time
import requests
import os
from typing import Tuple
from dotenv import load_dotenv

from core.custom_exceptions.general_exceptions import GenericAPIException

load_dotenv()

REMOTE_CHECK_APIKEY = os.environ["REMOTECHECKAPIKEY"]
APP_SHEET_ACCESS_KEY = os.environ["APPSHEETACCESSKEY"]
SWD_SHOPKEY = os.environ["SWDSHOPKEY"]
SWD_SHOPID = os.environ["SWDSHOPID"]
APP_AUTH_TOKEN = os.environ["APPAUTHTOKEN"]


# utility function for swd authentication
def generateSalt() -> str:
    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(128 // 8))


# utility function for swd authentication
def generateHash(timestamp, salt) -> str:
    return hmac.new(
        msg=f"{SWD_SHOPID}{SWD_SHOPKEY}{timestamp}{salt}".encode(),
        key=SWD_SHOPKEY.encode(), digestmod=hashlib.sha512).hexdigest()


# utility for swd auth
def generateSWDAuthJson():
    timestamp = int(time.time())
    salt = generateSalt()
    token = generateHash(timestamp=timestamp, salt=salt)
    return {
        "shopid": SWD_SHOPID,
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
            "company": formattedOrder["company"] if formattedOrder["company"] else None,
            "street": f"{formattedOrder['shipping_address1']},{formattedOrder['shipping_address2']}",
            "box": "",
            "zip": formattedOrder["shipping_postal_code"],
            "city": formattedOrder["shipping_city"],
            "country_iso2": formattedOrder["shipping_country_code"],
            "phone": formattedOrder["shipping_phone_number"],
            "email": formattedOrder["customer_email"]
        },
        "items": items
    }


def performRemoteCheck(country: str, postal_code: str, shipper: str) -> int:
    headers = {"Tracking-Api-Key": REMOTE_CHECK_APIKEY}
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
        print(f"Stock check failed for {sku} Reason: {stockCheckResp.reason}")
        return False, "", ""

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
    createOrderResponse = requests.post(url="https://api1.shopwedo.com/api/createOrder", data=formData)
    return createOrderResponse


def performSWDGetOrder(orderID: str) -> requests.Response:
    formData = {"auth": json.dumps(generateSWDAuthJson()),
                "data": json.dumps({
                    "external_order_id": orderID
                })}
    return requests.post(url="https://api1.shopwedo.com/api/getOrder", data=formData)


def performAuthTest() -> requests.Response:
    data = {"auth": json.dumps(generateSWDAuthJson())}
    return requests.post(url="https://admin.shopwedo.com/api/authTest", data=data)