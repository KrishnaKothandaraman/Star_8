import datetime
import json
import requests

from core.custom_exceptions.general_exceptions import GenericAPIException
from core.marketplace_clients.clientinterface import MarketPlaceClient
from get_order_history import keys


class RefurbedClient(MarketPlaceClient):
    key: str
    vendor: str

    def __init__(self, key: str, dateFieldName: str, itemKeyName: str, dateStringFormat: str):
        super().__init__(key)
        self.vendor = "Refurbed"
        self.dateFieldName = dateFieldName
        self.dateStringFormat = dateStringFormat
        self.itemKeyName = itemKeyName

    def getOrdersBetweenDates(self, start: datetime.datetime, end: datetime.datetime):
        """
        :param start: ISO 8601 format date string
        :param end: ISO 8601 format date string
        :return: response
        """
        start = self.convertDateTimeToString(start, "T00:00:00.00000Z")
        end = self.convertDateTimeToString(end, "T23:59:59.9999Z")

        print(start, end)
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

    def getOrderByID(self, orderID):
        print(f"INFO: Sending request to RF")

        resp = requests.post(url="https://api.refurbed.com/refb.merchant.v1.OrderService/ListOrders",
                             headers={
                                 "Authorization": self.key}, data=json.dumps({"id": str(orderID)}))

        if resp.status_code != 200:
            raise GenericAPIException(resp.reason)

        return resp.json()

#
# RFAPIInstance = RefurbedClient(key=keys["RF"]["token"], itemKeyName="items",
#                                dateFieldName="released_at", dateStringFormat="%Y-%m-%dT%H:%M:%S.%fZ")
# print(RFAPIInstance.getOrderByID(2584017))
