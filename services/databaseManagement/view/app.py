from core.custom_exceptions.general_exceptions import IncorrectSheetTitleException
import time
import traceback
from flask_cors import CORS, cross_origin
import googleapiclient.errors
from flask import Flask, request, make_response, jsonify, send_file
from core.google_services.googleSheetsService import GoogleSheetsService
import services.databaseManagement.controller.orders_controller as orders_controller
from core.marketplace_clients.bmclient import BackMarketClient
from core.marketplace_clients.rfclient import RefurbedClient
from get_order_history import keys

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/update-googlesheet', methods=['POST'])
def updateGoogleSheet():
    start = time.time()
    try:
        service = GoogleSheetsService()
    except Exception:
        print(traceback.print_exc())
        return make_response(jsonify({"type": "fail",
                                      "message": "Failed to open Google Sheets. Check server logs for more info"
                                      }),
                             400)
    try:
        RFAPIInstance = RefurbedClient(key=keys["RF"]["token"], itemKeyName="items",
                                       dateFieldName="released_at", dateStringFormat="%Y-%m-%dT%H:%M:%S.%fZ")
        BMAPIInstance = BackMarketClient(key=keys["BM"]["token"], itemKeyName="orderlines",
                                         dateFieldName="date_creation", dateStringFormat="%Y-%m-%dT%H:%M:%S%z")

        recordsUpdated = orders_controller.performUpdateExistingOrdersUpdate(service=service,
                                                                             BMAPIInstance=BMAPIInstance,
                                                                             RFAPIInstance=RFAPIInstance)

        newRecordsAdded = orders_controller.performAddNewOrdersUpdate(service=service,
                                                                      BMAPIInstance=BMAPIInstance,
                                                                      RFAPIInstance=RFAPIInstance)

        end = time.time()

        print(f"Time taken to handle this request {end - start}")

        return make_response(jsonify({"type": "success",
                                      "message": f"Added {newRecordsAdded} records! Updated {recordsUpdated} records!"
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
