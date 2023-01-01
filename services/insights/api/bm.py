import requests
from pandas import to_datetime as to_datetime
from core.custom_exceptions.general_exceptions import GenericAPIException
from get_order_history import keys


def getBMOrdersBetweenDates(start, end):

    print(f"INFO: Sending request to BM")
    nextURL = f"https://www.backmarket.fr/ws/orders?date_creation={start}"
    numOrders = 0
    orders = []

    while nextURL:
        print(f"Making call to {nextURL}")
        resp = requests.get(url=nextURL,
                            headers={"Authorization": f"basic {keys['BM']['token']}"})
        if resp.status_code != 200:
            print(f"Error occured {resp.status_code}")
            raise GenericAPIException(resp.reason)

        nextURL = resp.json()["next"]
        numOrders += len(resp.json()["results"])
        orders += [res for res in resp.json()["results"] if to_datetime(res["date_creation"]).strftime("%Y-%m-%d %H:%M:%S") <= end]

    print(f"{numOrders=}")
    return orders
