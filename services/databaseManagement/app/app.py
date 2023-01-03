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
BM_SPREADSHEET_ID = "1BhDJ-RJwbq6wQtAsoZoN5YY5InK5Z2Qc15rHgLzo4Ys"
BM_SPREADSHEET_NAME = "OrderS"
RF_SPREADSHEET_ID = "1BhDJ-RJwbq6wQtAsoZoN5YY5InK5Z2Qc15rHgLzo4Ys"
RF_SPREADSHEET_NAME = "RF_Orders"


def convertBetweenDateTimeStringFormats(inputString: str, inputFormat: str, outputFormat: str) -> str:
    return datetime.datetime.strptime(inputString, inputFormat).strftime(outputFormat)


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
        googleSheetOrderIDs = service.getEntireColumnData(sheetID=RF_SPREADSHEET_ID, sheetName=RF_SPREADSHEET_NAME,
                                                          column="A")
        googleSheetOrderIDs = {item[0] for item in googleSheetOrderIDs[1:] if len(item) > 0}

        RFAPIInstance = RefurbedClient(key=keys["RF"]["token"])
        todayStartDateTime = (datetime.datetime.now()).strftime("%Y-%m-%d") + "T00:00:00.00000Z"
        todayEndDateTime = datetime.datetime.now().strftime("%Y-%m-%d") + "T23:59:59.9999Z"
        RFNewOrders = RFAPIInstance.getOrdersBetweenDates(start=todayStartDateTime, end=todayEndDateTime)
        ordersToBeAdded = []
        for order in RFNewOrders:
            if str(order["id"]) not in googleSheetOrderIDs:
                ordersToBeAdded.append(order)
        """
        Step 1 is to flatten everything except the orderlines
        """
        # contains flattened order list to upload to sheets
        flattenedOrderList = []

        # for each order that may contain multiple orderlines
        for order in ordersToBeAdded:
            # add supplement address field to clean code to clean code
            order["shipping_address"].setdefault("supplement", "")
            order["invoice_address"].setdefault("supplement", "")
            order["invoice_address"].setdefault("company_vatin", "")

            order["shipping_address"].pop("company_name", None)
            order["invoice_address"].pop("company_name",None)

            #print(len(order.keys()), len(order["shipping_address"].keys()), len(order["invoice_address"].keys()))
            # for each orderline in an order
            for i, _ in enumerate(order["items"]):
                # create a row
                singleFlatOrder = []
                for key, item in order.items():
                    if key != "items":
                        if type(item) != dict:
                            item = convertBetweenDateTimeStringFormats(item, "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d %H:%M:%S") if key == "released_at" else item
                            singleFlatOrder.append(str(item))
                        else:
                            singleFlatOrder += [str(val) for _, val in item.items()]
                    # only add the current ith orderline to this row
                    else:
                        singleFlatOrder += [val for _, val in order["items"][i].items()]
                flattenedOrderList.append(singleFlatOrder)

        service.appendValuesToBottomOfSheet(data=flattenedOrderList, sheetTitle=RF_SPREADSHEET_NAME,
                                            documentID=RF_SPREADSHEET_ID)
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
        todayStartDateTime = datetime.datetime.now().strftime("%Y-%m-%d") + " 00:00:00"
        todayEndDateTime = datetime.datetime.now().strftime("%Y-%m-%d") + " 23:59:59"
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
