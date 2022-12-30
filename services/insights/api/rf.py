import json

import requests

from get_order_history import keys


def getRFOrdersAfterDate(date):
    """

    :param date: ISO 8601 format date string
    :return: response
    """
    print(f"INFO: Sending request to RF")
    payload = {
        "filter": {
            "released_at": {
                "ge": date
            }
        }
    }
    resp = requests.post(url="https://api.refurbed.com/refb.merchant.v1.OrderService/ListOrders",
                         headers={
                             "Authorization": keys["RF"]["token"]}, data=json.dumps(payload))
    if resp.status_code != 200:
        print(f"Error occured {resp.status_code}")
        print(resp.reason)
        print(resp.content)
        exit(1)
    return resp.json()


