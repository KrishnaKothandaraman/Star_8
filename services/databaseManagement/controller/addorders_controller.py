import json

import requests

from core.custom_exceptions.general_exceptions import GenericAPIException
from core.marketplace_clients.bmclient import BackMarketClient
from get_order_history import keys


def performRemoteCheck(country: str, postal_code: str, shortshipper: str) -> int:
    headers = {"Tracking-Api-Key": keys["remote-check"]}
    body = {
        "country": f"{country}",
        "postal_code": f"{postal_code}",
        "courier_code": f"{shortshipper}"
    }
    remoteCheckResp = requests.post(url="https://api.trackingmore.com/v3/trackings/remote", headers=headers,
                                    data=json.dumps(body))
    if remoteCheckResp.status_code != 200:
        raise GenericAPIException("Remote check failed")

    return remoteCheckResp.json()["code"]


def performSWDAddOrder():
    bmClient = BackMarketClient(key=keys["BM"]["token"], itemKeyName="orderlines",
                                dateFieldName="date_creation", dateStringFormat="%Y-%m-%dT%H:%M:%S%z")

    newOrders = bmClient.getOrdersByState(state=1)

    for order in newOrders:
        country = order["shipping_address"]["country"]
        postal_code = order["shipping_address"]["postal_code"]
        courier_code = order["shipper"].split(" ")[0]
        remoteCheckCode = performRemoteCheck(country, postal_code, courier_code)
        print(remoteCheckCode)

performSWDAddOrder()