import os
import traceback
import services.database_management.app.controller.utils.swd_utils as swd_utils
import services.database_management.app.controller.utils.general_utils as general_utils
from typing import Tuple, List
from flask import request, make_response, jsonify
from core.custom_exceptions.general_exceptions import GenericAPIException, IncorrectAuthTokenException
from core.marketplace_clients.bmclient import BackMarketClient
from core.marketplace_clients.clientinterface import MarketPlaceClient
from core.marketplace_clients.rfclient import RefurbedClient
from dotenv import load_dotenv

load_dotenv()

APP_AUTH_TOKEN = os.environ["APPAUTHTOKEN"]


def isValidIMEI(imei: str) -> bool:
    return len(imei) == 15


def processPendingShipmentOrders(orders: List[dict], Client: MarketPlaceClient) -> int:
    updateCounter = 0
    for order in orders:
        formattedOrder = Client.convertOrderToSheetColumns(order)[0]
        print(f"Calling swd with {formattedOrder['order_id']}")
        swdGetOrder = swd_utils.performSWDGetOrder(orderID=formattedOrder["order_id"])

        if swdGetOrder.status_code != 200:
            print(f"OrderID {formattedOrder['order_id']} not found in swd")
            continue

        swdRespBody = swdGetOrder.json()[0][0]

        if not swdRespBody["shipping"]:
            print(f"OrderID {formattedOrder['order_id']} not shipped yet")
            continue

        for item in swdRespBody["items"]:
            if not item["serialnumber"] or not item["picked"]:
                continue

            trackingData = Client.getBodyForUpdateStateToShippedRequest(order=formattedOrder,
                                                                        item=item,
                                                                        swdRespBody=swdRespBody)

            resp = Client.MakeUpdateOrderStateByOrderIDRequest(formattedOrder["order_id"], trackingData)
            print(resp.status_code)
            if resp.status_code != 200:
                print(f"Update tracking info for {formattedOrder['order_id']} failed. {resp.reason}")
                general_utils.updateAppSheetWithRows(rows=[{"order_id": int(formattedOrder["order_id"]),
                                                            "Note": f"Upload tracking info failed. Error code: {resp.status_code}"
                                                                    f",Error json {resp.reason}"
                                                            }]
                                                     )
            else:
                print(f"Upload tracking info for {formattedOrder['order_id']} successful")
                general_utils.updateAppSheetWithRows(rows=[{"order_id": int(formattedOrder["order_id"]),
                                                            "Note": f"Done Upload the tracking Already "
                                                            }]
                                                     )
                updateCounter += 1
    return updateCounter


def updateTrackingInfo():
    try:
        key = request.headers.get('auth-token')

        if not key or key != APP_AUTH_TOKEN:
            raise IncorrectAuthTokenException("Incorrect auth token provided")

        BMClient = BackMarketClient()
        RFClient = RefurbedClient()

        numNewOrders = 0

        BMPendingShipmentOrders = BMClient.getOrdersByState(state=3)
        numNewOrders += processPendingShipmentOrders(BMPendingShipmentOrders, BMClient)

        RFPendingShipmentOrders = RFClient.getOrdersByState(state="ACCEPTED")
        numNewOrders += processPendingShipmentOrders(RFPendingShipmentOrders, RFClient)

        return make_response(jsonify({"type": "success",
                                      "message": f"Updated {numNewOrders} new orders"
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
