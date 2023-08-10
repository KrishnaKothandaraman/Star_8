import os
import traceback
import werkzeug.exceptions
import services.database_management.app.controller.utils.swd_utils as swd_utils
import services.database_management.app.controller.utils.general_utils as general_utils
import services.database_management.app.controller.utils.repair_apps_utils as repair_apps_utils
from typing import Tuple, List, Optional, Dict, Literal
from flask import make_response, jsonify, request
from core.custom_exceptions.general_exceptions import GenericAPIException, IncorrectAuthTokenException, \
    StockAllocationFailedException
from core.marketplace_clients.bmclient import BackMarketClient
from core.marketplace_clients.clientinterface import MarketPlaceClient
from core.marketplace_clients.rfclient import RefurbedClient
from dotenv import load_dotenv
from flask_api import status

load_dotenv()

APP_AUTH_TOKEN = os.environ["APPAUTHTOKEN"]

sku_pair = Dict[Literal["old_sku", "new_sku"], str]


def processNewOrders(orders: List, client: MarketPlaceClient, replaced_sku: Optional[sku_pair] = None) -> int:
    """
    Performs logic to loop through orders and create SWD orders if stock exists
    :param orders: List of orders
    :param client: Marketplace that the orders are from
    :param replaced_sku: A pair of old_sku new_sku values
    :return:
    """
    update_counter = 0
    for order in orders:
        formatted_order = client.convertOrderToSheetColumns(order)[0]
        # remoteCheckCode = swd_utils.performRemoteCheck(country=formattedOrder["shipping_country_code"],
        #                                                postal_code=formattedOrder["shipping_postal_code"],
        #                                                shipper=formattedOrder["shipper"].split(" ")[0])

        formatted_order["shipper"] = general_utils.getShipperName(price=float(formatted_order["total_charged"]),
                                                                  chosenShipperName=formatted_order["shipper"],
                                                                  country_code=formatted_order["shipping_country_code"])

        order_items = client.getOrderItems(order)
        current_order_id = formatted_order['order_id']
        order_created = False

        stock_allocated, swd_model_names = swd_utils.perform_swd_stock_check_for_order_items(client, order_items)

        if stock_allocated:
            """Stock allocated for order in SWD successfully"""
            print(f"Stock exists for order {current_order_id} in SWD")
            swd_items_body = client.generateItemsBodyForSWDCreateOrderRequest(order_items, swd_model_names)
            createOrderResp = swd_utils.performSWDCreateOrder(formatted_order, swd_items_body)
            if createOrderResp.status_code == 201:
                order_created = True
            else:
                print(f"Created order failed: Reason: {createOrderResp.reason}, JSON: {createOrderResp.json()}")
        else:
            try:
                repair_apps_utils.allocate_stock_for_order_items(client, order)
                order_created = True
            except StockAllocationFailedException as e:
                print(f"Stock allocation failed for order {current_order_id} with message: {e.args[0]}")
                continue
            except Exception as e:
                print(f"Stock allocation failed for order {current_order_id} with message: {e.args[0]}")
                traceback.print_exc()
                continue

        if order_created:
            if replaced_sku:
                client.updateSkuOfOrder(order, replaced_sku["new_sku"], replaced_sku["old_sku"])
            update_counter += client.updateStateOfOrder(order, "NEW", None)

    return update_counter


def swdAddManualOrder():
    try:
        body = request.json
        marketPlace = body["marketplace"]
        orderID = body["order_id"]
        oldSku = body["old_sku"]
        newSku = body["new_sku"]

        if marketPlace not in ("Refurbed", "Backmarket"):
            raise GenericAPIException(f"Invalid marketplace '{marketPlace}'. Marketplace must be either Refurbed,"
                                      f"Backmarket.")

        vendor = BackMarketClient() if marketPlace == "Backmarket" else RefurbedClient()

        order = vendor.getOrderByID(orderID, normalizeFields=True)
        vendor.updateSkuOfOrder(order, oldSku, newSku)
        processNewOrders([order], vendor, {"old_sku": oldSku, "new_sku": newSku})
        return make_response(jsonify({"type": "Success",
                                      "message": f"Order updated"
                                      }),
                             status.HTTP_200_OK)

    except KeyError as e:
        return make_response(jsonify({"type": "fail",
                                      "message": f"Key '{e.args[0]}' missing in request"
                                      }),
                             status.HTTP_400_BAD_REQUEST)
    except GenericAPIException as e:
        return make_response(jsonify({"type": "fail",
                                      "message": e.args[0]
                                      }),
                             status.HTTP_400_BAD_REQUEST)
    except werkzeug.exceptions.BadRequest:
        return make_response(jsonify({"type": "fail",
                                      "message": "JSON Body required in request"
                                      }),
                             status.HTTP_400_BAD_REQUEST)


def swdAddOrder():
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
            numNewOrders += processNewOrders([newOrder], vendor)
        else:
            RFNewOrders = RFClient.getOrdersByState(state="NEW")
            numNewOrders += processNewOrders(RFNewOrders, RFClient)
            BMNewOrders = BMClient.getOrdersByState(state=1)
            numNewOrders += processNewOrders(BMNewOrders, BMClient)
        return make_response(jsonify({"type": "success",
                                      "message": f"Updated {numNewOrders} new orders"
                                      }),
                             200)
    except GenericAPIException as e:
        return make_response(jsonify({"type": "fail",
                                      "message": "Order id not found in marketplace"
                                      }),
                             400)
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
