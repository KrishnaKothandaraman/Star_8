import os
import traceback
import werkzeug.exceptions
import services.database_management.app.controller.utils.swd_utils as swd_utils
import services.database_management.app.controller.utils.general_utils as general_utils
from typing import Tuple, List
from flask import request, make_response, jsonify
from core.custom_exceptions.general_exceptions import IncorrectAuthTokenException, GenericAPIException
from core.marketplace_clients.bmclient import BackMarketClient
from core.marketplace_clients.clientinterface import MarketPlaceClient
from core.marketplace_clients.rfclient import RefurbedClient
from services.database_management.app.controller.utils.swd_utils import SWDShippingData
from dotenv import load_dotenv

load_dotenv()

APP_AUTH_TOKEN = os.environ["APPAUTHTOKEN"]


def isValidIMEI(imei: str) -> bool:
    return len(imei) == 15


def processPendingShipmentOrders(orders: List[dict], Client: MarketPlaceClient) -> int:
    updateCounter = 0
    for order in orders:
        formattedOrders = Client.convertOrderToSheetColumns(order)
        orderID = formattedOrders[0]['order_id']
        print(f"Calling swd with {orderID}")
        swdGetOrder = swd_utils.performSWDGetOrder(orderID=orderID)
        if swdGetOrder.status_code != 200:
            print(f"OrderID {orderID} not found in swd")
            continue

        swdRespBody = swdGetOrder.json()[0][0]
        if not swdRespBody["shipping"]:
            print(f"OrderID {orderID} not shipped yet")
            continue
        processedSerialNumbers = set()
        shippingDataForOrderList: List[SWDShippingData] = []
        for item in swdRespBody["items"]:
            if not item["serialnumber"] or not item["picked"]:
                continue
            try:
                # set because swd sometimes scan the same serialnumber twice
                for serial_num in set(item["serialnumber"]):
                    if serial_num in processedSerialNumbers:
                        continue
                    processedSerialNumbers.add(serial_num)
                    shippingDataForOrderList.append(SWDShippingData(
                        order_id=orderID,
                        item_id=item["external_orderline_id"],
                        sku=[order["sku"] for order in formattedOrders if str(order["item_id"]) == str(item["external_orderline_id"])][0],
                        serial_number=serial_num,
                        shipper=swdRespBody["shipping"][0]["provider"].split("express")[0],
                        tracking_number=swdRespBody["shipping"][0]["code"],
                        tracking_url=swdRespBody["shipping"][0]["tracking_url"],
                        is_multi_sku=True if len(set(item["serialnumber"])) > 1 else False
                    ))
                    break
            except IndexError:
                print(f"{orderID} was done using old API")
                continue
        for shipping_data in shippingDataForOrderList:
            trackingData = Client.getBodyForUpdateStateToShippedRequest(shipping_data=shipping_data)
            resp = Client.MakeUpdateOrderStateByOrderIDRequest(shipping_data.order_id, trackingData)
            if resp.status_code != 200:
                print(f"Update tracking info for {shipping_data.order_id} failed. {resp.reason}")
                print(resp.json())
                general_utils.updateAppSheetWithRows(rows=[{"order_id": int(shipping_data.order_id),
                                                            "Note": f"Upload tracking info failed. Error code: {resp.status_code}"
                                                                    f",Error json {resp.reason}"
                                                            }]
                                                     )
            else:
                print(f"Upload tracking info for {shipping_data.order_id} successful")
                general_utils.updateAppSheetWithRows(rows=[{"order_id": int(shipping_data.order_id),
                                                            "Note": f"Done Upload the tracking Already "
                                                            }]
                                                     )
                updateCounter += 1
    return updateCounter


def updateTrackingInfo():
    try:
        body = request.json
    except werkzeug.exceptions.BadRequest:
        body = None
    try:
        key = request.headers.get('auth-token')

        if not key or key != APP_AUTH_TOKEN:
            raise IncorrectAuthTokenException("Incorrect auth token provided")

        BMClient = BackMarketClient()
        RFClient = RefurbedClient()

        numNewOrders = 0
        if body:
            print("Processing single order")
            singleOrderID = body["single_order_id"]
            vendor = BMClient if body["vendor"] == "Backmarket" else RFClient
            newOrder = vendor.getOrderByID(orderID=singleOrderID)
            numNewOrders += processPendingShipmentOrders([newOrder], vendor)
        else:
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
    except GenericAPIException as e:
        if body and e.args[0] == "Not Found":
            print(traceback.print_exc())
            return make_response(jsonify({"type": "fail",
                                          "message": "Incorrect Vendor for single order ID"
                                          }),
                                 400)
        else:
            return make_response(jsonify({"type": "fail",
                                          "message": "Contact support. Check server logs"
                                          }),
                                 500)
    except Exception:
        print(traceback.print_exc())
        return make_response(jsonify({"type": "fail",
                                      "message": "Contact support. Check server logs"
                                      }),
                             500)
