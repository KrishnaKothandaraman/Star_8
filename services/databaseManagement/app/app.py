import sys
import os
# add root to paths
sys.path.append(os.path.join(""))


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
        googleSheetItems = service.getEntireColumnData(sheetID=SPREADSHEET_ID, sheetName="OrderS", column="A")
        googleSheetItems = {item[0] for item in googleSheetItems[1:] if len(item) > 0}

        BMAPIInstance = BackmarketAPI()
        newOrders = BMAPIInstance.getOrdersFromToday()
        ordersToBeAdded = []
        for order in newOrders:
            if order["order_id"] not in googleSheetItems:
                print(f"{order['order_id']} not in google sheet!")
                ordersToBeAdded.append(order)

        end = time.time()

        print(f"Time taken to handle this request {end - start}")

        return make_response(jsonify({"type": "success",
                                      "data": []
                                      }),
                             200)
    except googleapiclient.errors.HttpError as e:
        return make_response(jsonify({"type": "fail",
                                      "message": e.reason
                                      }),
                             400)
    except Exception:
        print(traceback.print_exc())
        return make_response(jsonify({"type": "fail",
                                      "message": "Contact support. Check server logs"
                                      }),
                             400)

        # replaces all optional parameters
        replaceTextRequests = service.makeReplaceTextRequests(data=optionalParameters)

        service.executeBatchRequest(requests=replaceTextRequests, documentId=templateCopyID)

        if orders != None:
            # creates table
            service.createTableFromOrders(orders=orders, documentID=templateCopyID)

        # gets pdf binary
        fileBytesIO = service.downloadDocument(fileId=templateCopyID)

        response = make_response(fileBytesIO)

        if template_type == "docs":
            response.headers.set('Content-Type', 'application/pdf')
            response.headers.set(
                'Content-Disposition', 'attachment', filename="invoice.pdf")

        else:
            response.headers.set('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response.headers.set(
                'Content-Disposition', 'attachment', filename="invoice.xlsx")

        return response
    except FileNotFoundError:
        traceback.print_exc()
        return make_response(jsonify({"type": "fail",
                                      "message": "Internal server error"
                                      }),
                             500)
    except googleapiclient.errors.HttpError as e:
        traceback.print_exc()
        return make_response(jsonify({"type": "fail",
                                      "message": "Invalid template ID",
                                      }),
                             400)
    except Exception as e:
        traceback.print_exc()
        return make_response(jsonify({"type": "fail",
                                      "message": "Internal Server Error",
                                      }),
                             500)


if __name__ == '__main__':
    # **** if you run locally without dockerfile, uncomment the below lines *****
    # os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.getcwd(), "../helloar-analytics-d4298ceae005.json")
    # os.environ["SENDGRID_API_KEY"] = "<enter api key here>"
    app.run(port=5001)
