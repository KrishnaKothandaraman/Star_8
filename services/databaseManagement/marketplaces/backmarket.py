import sys
import os
sys.path.append(os.path.join(""))

from datetime import datetime, timedelta
from services.databaseManagement.marketplaces.interface import APIInterface
from get_order_history import keys
from core.custom_exceptions.general_exceptions import GenericAPIException
import requests


class BackmarketAPI(APIInterface):
    def getOrdersFromToday(self):
        # make date string required by BM. Set timing to midnight for getting all orders on that day
        today_date = datetime.today().strftime("%Y-%m-%d") + " 00:00:01"
        print(f"Getting orders from {today_date}")

        print(f"INFO: Sending request to BM")

        resp = requests.get(url=f"https://www.backmarket.fr/ws/orders?date_creation={today_date}",
                            headers={"Authorization": f"basic {keys['BM']['token']}"})
        if resp.status_code != 200:
            raise GenericAPIException(f"Error occured {resp.status_code}")

        return resp.json()["results"]
