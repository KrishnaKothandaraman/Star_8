from core.custom_exceptions.general_exceptions import IncorrectAuthTokenException
from core.custom_exceptions.google_service_exceptions import IncorrectSheetTitleException
import time
import traceback
from flask_cors import CORS, cross_origin
import werkzeug.exceptions as HTTPExceptions
import googleapiclient.errors
from flask import Flask, request, make_response, jsonify, send_file
from core.google_services.googleSheetsService import GoogleSheetsService
import services.databaseManagement.controller.orders_database_controller as ordersdb_controller
import services.databaseManagement.controller.addorders_controller as addorders_controller
from core.marketplace_clients.bmclient import BackMarketClient
from core.marketplace_clients.rfclient import RefurbedClient
from keys import keys

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/update-googlesheet', methods=['POST'])
def updateGoogleSheet():
    try:
        key = request.headers.get('auth-token')

        body = request.get_json()
        numberOfDaysToUpdate = body["days"] if "days" in body else 0

        if not key or key != keys["auth-token"]:
            raise IncorrectAuthTokenException("Incorrect auth token provided")

        start = time.time()
        service = GoogleSheetsService()
        RFAPIInstance = RefurbedClient(key=keys["RF"]["token"], itemKeyName="items",
                                       dateFieldName="released_at", dateStringFormat="%Y-%m-%dT%H:%M:%S.%fZ")
        BMAPIInstance = BackMarketClient(key=keys["BM"]["token"])

        recordsUpdated = ordersdb_controller.performUpdateExistingOrdersUpdate(service=service,
                                                                               BMAPIInstance=BMAPIInstance,
                                                                               RFAPIInstance=RFAPIInstance)
        newRecordsAdded = ordersdb_controller.performAddNewOrdersUpdate(service=service,
                                                                        BMAPIInstance=BMAPIInstance,
                                                                        RFAPIInstance=RFAPIInstance,
                                                                        days=numberOfDaysToUpdate)

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
    except IncorrectAuthTokenException as e:
        return make_response(jsonify({"type": "fail",
                                      "message": e.args[0]
                                      }),
                             401)
    except HTTPExceptions.BadRequest as e:
        return make_response(jsonify({"type": "Bad Request",
                                      "message": "No JSON body in request"
                                      }),
                             400)
    except Exception:
        print(traceback.print_exc())
        return make_response(jsonify({"type": "fail",
                                      "message": "Contact support. Check server logs"
                                      }),
                             500)


@app.route("/swd-add-order", methods=["POST"])
def swdAddOrder():
    try:
        key = request.headers.get('auth-token')

        if not key or key != keys["auth-token"]:
            raise IncorrectAuthTokenException("Incorrect auth token provided")

        addorders_controller.performSWDAddOrder()

        return make_response(jsonify({"type": "success",
                                      "message": "Done"
                                      }),
                             200)

    except IncorrectAuthTokenException as e:
        return make_response(jsonify({"type": "fail",
                                      "message": e.args[0]
                                      }),
                             401)
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
