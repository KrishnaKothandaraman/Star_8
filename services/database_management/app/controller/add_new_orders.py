import os
import traceback
import services.database_management.app.controller.utils.swd_utils as swd_utils
import services.database_management.app.controller.utils.general_utils as general_utils
from typing import Tuple, List
from flask import make_response, jsonify, request
from core.custom_exceptions.general_exceptions import GenericAPIException, IncorrectAuthTokenException
from core.marketplace_clients.bmclient import BackMarketClient
from core.marketplace_clients.clientinterface import MarketPlaceClient
from core.marketplace_clients.rfclient import RefurbedClient
from dotenv import load_dotenv

load_dotenv()

APP_AUTH_TOKEN = os.environ["APPAUTHTOKEN"]


def processNewOrders(orders: List, MarketClient: MarketPlaceClient) -> int:
    """
    Performs logic to loop through orders and create SWD orders if stock exists
    :param orders: List of orders
    :param MarketClient: Marketplace that the orders are from
    :return:
    """
    updateCounter = 0
    for order in orders:
        formattedOrder = MarketClient.convertOrderToSheetColumns(order)[0]
        remoteCheckCode = swd_utils.performRemoteCheck(country=formattedOrder["shipping_country_code"],
                                                       postal_code=formattedOrder["shipping_postal_code"],
                                                       shipper=formattedOrder["shipper"].split(" ")[0])
        stockExists, swdModelName, stockAmount = "", "", ""

        formattedOrder["shipper"] = general_utils.getShipperName(price=float(formattedOrder["total_charged"]),
                                                                 chosenShipperName=formattedOrder["shipper"],
                                                                 country_code=formattedOrder["shipping_country_code"],
                                                                 remoteCheckCode=remoteCheckCode)
        print(
            f"For {formattedOrder['order_id']} to country {formattedOrder['shipping_country_code']}, set shipper to {formattedOrder['shipper']}")
        orderItems = MarketClient.getOrderItems(order)
        for orderline in orderItems:
            listing = MarketClient.getSku(orderline)
            stockExists, swdModelName, stockAmount = swd_utils.performSWDStockCheck(listing)
            if not stockExists:
                general_utils.updateAppSheetWithRows(rows=[{"order_id": MarketClient.getOrderID(order),
                                                            "Note": f"This Over _sell  {listing}  need ask the Buyer change to "
                                                                    f"other: / some Stock waiting Book in / "
                                                            }]
                                                     )
                break

        # else here means the orderline loop was excited normally. No break
        else:
            print(f"All stock exists for order {swdModelName}")
            SWDItemsBody = MarketClient.generateItemsBodyForSWDCreateOrderRequest(orderItems, swdModelName)
            createOrderResp = swd_utils.performSWDCreateOrder(formattedOrder, SWDItemsBody)
            if createOrderResp.status_code != 201:
                print(f"Created order failed due to {createOrderResp.reason}")
                general_utils.updateAppSheetWithRows(rows=[{"order_id": formattedOrder["order_id"],
                                                            "Note": f"Shop we do add order failed. Error code: {createOrderResp.status_code}"
                                                                    f",Error json {createOrderResp.reason}"
                                                            }]
                                                     )
            else:
                updateCounter += MarketClient.updateStateOfOrder(order, "NEW", None)
    return updateCounter


def swdAddOrder():
    try:
        key = request.headers.get('auth-token')

        if not key or key != APP_AUTH_TOKEN:
            raise IncorrectAuthTokenException("Incorrect auth token provided")

        BMClient = BackMarketClient()
        RFClient = RefurbedClient()

        numNewOrders = 0

        BMNewOrders = BMClient.getOrdersByState(state=1)
        numNewOrders += processNewOrders(BMNewOrders, BMClient)

        RFNewOrders = RFClient.getOrdersByState(state="NEW")
        numNewOrders += processNewOrders(RFNewOrders, RFClient)

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
