import requests
from get_order_history import keys


def getBMOrdersAfterDate(date):

    print(f"INFO: Sending request to BM")
    nextURL = f"https://www.backmarket.fr/ws/orders?date_creation={date}"
    numOrders = 0
    orders = []

    while nextURL:
        print(f"Making call to {nextURL}")
        resp = requests.get(url=nextURL,
                            headers={"Authorization": f"basic {keys['BM']['token']}"})
        if resp.status_code != 200:
            print(f"Error occured {resp.status_code}")

        nextURL = resp.json()["next"]
        numOrders += len(resp.json()["results"])
        orders += resp.json()["results"]
        break
    print(f"{numOrders=}")
    return orders
