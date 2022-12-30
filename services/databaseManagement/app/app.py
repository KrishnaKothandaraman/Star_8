import sys
import os
# add root to paths
from typing import Dict
from core.custom_exceptions.general_exceptions import IncorrectSheetTitleException
import time
import json
import traceback
from flask_cors import CORS, cross_origin
import googleapiclient.errors
from flask import Flask, request, make_response, jsonify, send_file
import requests
from core.google_services.googleSheetsService import GoogleSheetsService
from services.databaseManagement.marketplaces.backmarket import BackmarketAPI

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

GOOGLE_DOCS_MIMETYPE = "application/vnd.google-apps.document"
GOOGLE_SHEETS_MIMETYPE = "application/vnd.google-apps.spreadsheet"
SPREADSHEET_ID = "1BhDJ-RJwbq6wQtAsoZoN5YY5InK5Z2Qc15rHgLzo4Ys"
SPREADSHEET_NAME = "OrderS"


@app.route('/update-bm-googlesheet', methods=['POST'])
def updateBMGoogleSheet():
    start = time.time()
    try:
        service = GoogleSheetsService()
    except Exception as e:
        print(traceback.print_exc())
        return make_response(jsonify({"type": "fail",
                                      "message": "Failed to open Google Sheets. Check server logs for more info"
                                      }),
                             400)

    try:
        googleSheetOrderIDs = service.getEntireColumnData(sheetID=SPREADSHEET_ID, sheetName=SPREADSHEET_NAME,
                                                          column="A")
        googleSheetOrderIDs = {item[0] for item in googleSheetOrderIDs[1:] if len(item) > 0}

        BMAPIInstance = BackmarketAPI()
        newOrders = BMAPIInstance.getOrdersFromToday()
        ordersToBeAdded = []
        for order in newOrders:
            if str(order["order_id"]) not in googleSheetOrderIDs:
                ordersToBeAdded.append(order)
        """
        Step 1 is to flatten everything except the orderlines
        """
        # contains flattened order list to upload to sheets
        flattenedOrderList = []

        # for each order that may contain multiple orderlines
        for order in ordersToBeAdded:
            # for each orderline in an order
            for i, _ in enumerate(order["orderlines"]):
                # create a row
                singleFlatOrder = []
                for key, item in order.items():

                    if key != "orderlines":
                        if type(item) != dict:
                            singleFlatOrder.append(item)
                        else:
                            for _, val in item.items():
                                singleFlatOrder.append(val)

                    # only add the current ith orderline to this row
                    else:
                        for _, val in order["orderlines"][i].items():
                            singleFlatOrder.append(val)
                flattenedOrderList.append(singleFlatOrder)

        service.appendValuesToBottomOfSheet(data=flattenedOrderList, sheetTitle=SPREADSHEET_NAME,
                                            documentID=SPREADSHEET_ID)
        end = time.time()

        print(f"Time taken to handle this request {end - start}")

        return make_response(jsonify({"type": "success",
                                      "message": f"Added {len(flattenedOrderList)} records!"
                                      }),
                             200)
    except googleapiclient.errors.HttpError as e:
        return make_response(jsonify({"type": "fail",
                                      "message": e.reason
                                      }),
                             400)
    except IncorrectSheetTitleException as e:
        return make_response(jsonify({"type": "fail",
                                      "message": e.args[0]
                                      }),
                             400)
    except Exception:
        print(traceback.print_exc())
        return make_response(jsonify({"type": "fail",
                                      "message": "Contact support. Check server logs"
                                      }),
                             500)


if __name__ == '__main__':
    # **** if you run locally without dockerfile, uncomment the below lines *****
    # os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.getcwd(), "../helloar-analytics-d4298ceae005.json")
    # os.environ["SENDGRID_API_KEY"] = "<enter api key here>"
    app.run(port=5001)
