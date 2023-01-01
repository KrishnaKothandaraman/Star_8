import json
import time

import requests
import sys

sys.path.append("")
from get_order_history import keys


def getRFOrdersBetweenDates(startDate, endDate):
    """

    :param date: ISO 8601 format date string
    :return: response
    """
    print(f"INFO: Sending request to RF")
    orders = []
    payload = {
        "filter": {
            "released_at": {
                "ge": startDate,
                "le": endDate
            }
        },
    }
    while True:
        print(f"Making Request")

        resp = requests.post(url="https://api.refurbed.com/refb.merchant.v1.OrderService/ListOrders",
                             headers={
                                 "Authorization": keys["RF"]["token"]}, data=json.dumps(payload))
        if resp.status_code != 200:
            print(f"Error occured {resp.status_code}")
            print(resp.reason)
            print(resp.content)
            exit(1)

        resp_json = resp.json()
        orders += resp_json["orders"]
        if resp_json["has_more"]:
            starting_after = resp_json['orders'][-1]['id']
            payload = {
                "filter": {
                    "released_at": {
                        "ge": startDate,
                        "le": endDate
                    }
                },
                "pagination": {
                    "starting_after": str(starting_after)
                }
            }
        else:
            break

    print(f"Number of orders {len(orders)}")
    return orders
