import hashlib
import hmac
import json
import os
import random
import string
import time
import traceback
import requests
from typing import Tuple, List
from flask import make_response, jsonify, request
from core.custom_exceptions.general_exceptions import GenericAPIException, IncorrectAuthTokenException
from core.marketplace_clients.bmclient import BackMarketClient
from core.marketplace_clients.clientinterface import MarketPlaceClient
from core.marketplace_clients.rfclient import RefurbedClient
from dotenv import load_dotenv

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
            "company": formattedOrder["company"],
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


def updateAppSheetWithRows(rows: List):
    print(f"Updated sheet! with {rows}")
    return
    requests.post(
        url='https://api.appsheet.com/api/v2/apps/6aec3910-fe2b-4d41-840e-aee105698fe3/tables/Order_Notice/Add',
        headers={'Content-Type': 'application/json',
                 'applicationAccessKey': APP_SHEET_ACCESS_KEY},
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
    createOrderResponse = requests.post(url="https://admin.shopwedo.com/api/createOrder", data=formData)
    return createOrderResponse


def getShipperName(price: float, chosenShipperName: str, country_code: str, remoteCheckCode):
    # last condition in the IF is to filter out any shippers such as UPS Express or DHL Express
    if price < 800 and remoteCheckCode == 204 and len(chosenShipperName.split(" ")) == 1 and country_code != "ES":
        return "ups"
    else:
        return "dhlexpress"


def processNewOrders(orders: List, MarketClient: MarketPlaceClient) -> int:
    """
    Performs logic to loop through orders and create SWD orders if stock exists
    :param orders: List of orders
    :param MarketClient: Marketplace that the orders are from
    :return:
    """
    updateCounter = 0
    for order in orders:
        formattedOrder = MarketClient.convertOrderToSheetColumns(order)[0]
        remoteCheckCode = performRemoteCheck(country=formattedOrder["shipping_country_code"],
                                             postal_code=formattedOrder["shipping_postal_code"],
                                             shipper=formattedOrder["shipper"].split(" ")[0])
        stockExists, swdModelName, stockAmount = "", "", ""

        formattedOrder["shipper"] = getShipperName(price=float(formattedOrder["total_charged"]),
                                                   chosenShipperName=formattedOrder["shipper"],
                                                   country_code=formattedOrder["shipping_country_code"],
                                                   remoteCheckCode=remoteCheckCode)
        print(
            f"For {formattedOrder['order_id']} to country {formattedOrder['shipping_country_code']}, set shipper to {formattedOrder['shipper']}")
        orderItems = MarketClient.getOrderItems(order)
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
            SWDItemsBody = MarketClient.generateItemsBodyForSWDCreateOrderRequest(orderItems, swdModelName)
            createOrderResp = performSWDCreateOrder(formattedOrder, SWDItemsBody)
            if createOrderResp.status_code != 201:
                print(f"Created order failed due to {createOrderResp.reason}")
                updateAppSheetWithRows(rows=[{"order_id": formattedOrder["order_id"],
                                              "Note": f"Shop we do add order failed. Error code: {createOrderResp.status_code}"
                                                      f",Error json {createOrderResp.reason}"
                                              }]
                                       )
            else:
                updateCounter += MarketClient.updateStateOfOrder(order)
    return updateCounter


def swdAddOrder():
    try:
        key = request.headers.get('auth-token')

        if not key or key != APP_AUTH_TOKEN:
            raise IncorrectAuthTokenException("Incorrect auth token provided")

        BMClient = BackMarketClient()
        RFClient = RefurbedClient()

        numNewOrders = 0

        BMNewOrders = BMClient.getOrdersByState(state=1)
        numNewOrders += processNewOrders(BMNewOrders, BMClient)

        RFNewOrders = RFClient.getOrdersByState(state="NEW")
        numNewOrders += processNewOrders(RFNewOrders, RFClient)

        return make_response(jsonify({"type": "success",
                                      "message": f"Updated {numNewOrders} new orders"
                                      }),
                             200)

    except IncorrectAuthTokenException as e:
        return make_response(jsonify({"type": "fail",
                                      "message": e.args[0]
                                      }),
                             401)
    except Exception:
        print(traceback.print_exc())
        return make_response(jsonify({"type": "fail",
                                      "message": "Contact support. Check server logs"
                                      }),
                             500)

# performSWDAddOrder()
