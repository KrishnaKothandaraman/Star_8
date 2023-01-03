import json
import requests

from core.custom_exceptions.general_exceptions import GenericAPIException


class RefurbedClient:
    key: str

    def __init__(self, key):
        self.key = key

    def getOrdersBetweenDates(self, start, end):
        """
        :param start: ISO 8601 format date string
        :param end: ISO 8601 format date string
        :return: response
        """
        print(f"INFO: Sending request to RF")
        orders = []
        payload = {
            "filter": {
                "released_at": {
                    "ge": start,
                    "le": end
                }
            },
        }
        while True:
            print(f"Making Request")

            resp = requests.post(url="https://api.refurbed.com/refb.merchant.v1.OrderService/ListOrders",
                                 headers={
                                     "Authorization": self.key}, data=json.dumps(payload))
            if resp.status_code != 200:
                print(f"Error occured {resp.status_code}")
                raise GenericAPIException(resp.reason)

            resp_json = resp.json()
            orders += resp_json["orders"]
            if resp_json["has_more"]:
                starting_after = resp_json['orders'][-1]['id']
                payload["pagination"] = {"starting_after": str(starting_after)}
            else:
                break

        print(f"Refurbed {len(orders)}")
        return orders
