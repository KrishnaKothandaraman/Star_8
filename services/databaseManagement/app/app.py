import datetime

from core.custom_exceptions.general_exceptions import IncorrectSheetTitleException
import time
import traceback
from flask_cors import CORS, cross_origin
import googleapiclient.errors
from flask import Flask, request, make_response, jsonify, send_file
from core.google_services.googleSheetsService import GoogleSheetsService
from core.marketplace_clients.bmclient import BackMarketClient
from core.marketplace_clients.rfclient import RefurbedClient
from get_order_history import keys

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

GOOGLE_DOCS_MIMETYPE = "application/vnd.google-apps.document"
GOOGLE_SHEETS_MIMETYPE = "application/vnd.google-apps.spreadsheet"
SPREADSHEET_ID = "1BhDJ-RJwbq6wQtAsoZoN5YY5InK5Z2Qc15rHgLzo4Ys"
SPREADSHEET_NAME = "Combined_Orders"


@app.route('/update-rf-googlesheet', methods=['POST'])
def updateRFGoogleSheet():
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

        RFAPIInstance = RefurbedClient(key=keys["RF"]["token"], itemKeyName="items",
                                       dateFieldName="released_at", dateStringFormat="%Y-%m-%dT%H:%M:%S.%fZ")
        BMAPIInstance = BackMarketClient(key=keys["BM"]["token"], itemKeyName="orderlines",
                                         dateFieldName="date_creation", dateStringFormat="%Y-%m-%dT%H:%M:%S%z")

        nowDateTime = datetime.datetime.now() - datetime.timedelta(days = 1)
        RFNewOrders = RFAPIInstance.getOrdersBetweenDates(start=nowDateTime, end=nowDateTime)
        BMnewOrders = BMAPIInstance.getOrdersBetweenDates(start=nowDateTime, end=nowDateTime)

        ordersToBeAdded = {
            "BackMarket": [],
            "Refurbed": []
        }
        for order in RFNewOrders:
            if str(order["id"]) not in googleSheetOrderIDs:
                ordersToBeAdded["Refurbed"].append(order)

        for order in BMnewOrders:
            if str(order["order_id"]) not in googleSheetOrderIDs:
                ordersToBeAdded["BackMarket"].append(order)

        """
        Step 1 is to flatten everything except the orderlines
        """
        # contains flattened order list to upload to sheets
        flattenedOrderList = []

        convertedBMOrders = BMAPIInstance.convertOrdersToSheetColumns(ordersToBeAdded["BackMarket"])
        convertedRFOrders = RFAPIInstance.convertOrdersToSheetColumns(ordersToBeAdded["Refurbed"])

        flattenedOrderList += [list(d.values()) for d in convertedRFOrders + convertedBMOrders]

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
        googleSheetOrderIDs = service.getEntireColumnData(sheetID=BM_SPREADSHEET_ID, sheetName=BM_SPREADSHEET_NAME,
                                                          column="A")
        googleSheetOrderIDs = {item[0] for item in googleSheetOrderIDs[1:] if len(item) > 0}

        BMAPIInstance = BackMarketClient(key=keys["BM"]["token"])
        todayStartDateTime = datetime.datetime.now()
        todayEndDateTime = datetime.datetime.now()
        BMnewOrders = BMAPIInstance.getOrdersBetweenDates(start=todayStartDateTime, end=todayEndDateTime)
        ordersToBeAdded = []
        for order in BMnewOrders:
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
                            singleFlatOrder += [val for _, val in item.items()]
                    # only add the current ith orderline to this row
                    else:
                        singleFlatOrder += [val for _, val in order["orderlines"][i].items()]
                flattenedOrderList.append(singleFlatOrder)

        service.appendValuesToBottomOfSheet(data=flattenedOrderList, sheetTitle=BM_SPREADSHEET_NAME,
                                            documentID=BM_SPREADSHEET_ID)
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
