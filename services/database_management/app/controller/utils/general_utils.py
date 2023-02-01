import json
from typing import List

import requests
import os
from dotenv import load_dotenv

load_dotenv()
APP_SHEET_ACCESS_KEY = os.environ["APPSHEETACCESSKEY"]


def updateAppSheetWithRows(rows: List):
    resp = requests.post(
        url='https://api.appsheet.com/api/v2/apps/6aec3910-fe2b-4d41-840e-aee105698fe3/tables/Order_Notice/Add',
        headers={'Content-Type': 'application/json',
                 'applicationAccessKey': APP_SHEET_ACCESS_KEY},
        data=json.dumps({
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
        }))
    if resp.status_code == 200:
        print(f"Updated sheet! with {rows}. Response code {resp.status_code}")
    else:
        print(f"Update sheet failed! Code: {resp.status_code} message: {resp.reason}")


def getShipperName(price: float, chosenShipperName: str, country_code: str, remoteCheckCode):
    # last condition in the IF is to filter out any shippers such as UPS Express or DHL Express
    if price < 800 and remoteCheckCode == 204 and len(chosenShipperName.split(" ")) == 1 and \
            country_code not in ("ES", "SE"):
        return "ups"
    else:
        return "dhlexpress"
