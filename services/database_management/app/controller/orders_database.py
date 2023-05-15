import datetime
import os
from typing import Optional, List, Dict
from flask_api.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR
from core.custom_exceptions.general_exceptions import IncorrectAuthTokenException, GenericAPIException, \
    ResourceExhaustedException
from core.custom_exceptions.google_service_exceptions import IncorrectSheetTitleException
import time
import traceback
import werkzeug.exceptions as HTTPExceptions
import googleapiclient.errors
from flask import request, make_response, jsonify
from core.google_services.googleSheetsService import GoogleSheetsService
from core.marketplace_clients.bmclient import BackMarketClient
from core.marketplace_clients.clientinterface import MarketPlaceClient
from core.marketplace_clients.rfclient import RefurbedClient
from services.database_management.app.controller.utils.inventory_utils import CellData, FieldType

GOOGLE_DOCS_MIMETYPE = "application/vnd.google-apps.document"
GOOGLE_SHEETS_MIMETYPE = "application/vnd.google-apps.spreadsheet"
SPREADSHEET_ID = "19OXMfru14WMEI4nja9SCAljnCDrHlw33SHLO77vAmVo"
SPREADSHEET_NAME = "Combined_Orders"
TEST_SPREADSHEET_NAME = "tester"

APP_AUTH_TOKEN = os.environ["APPAUTHTOKEN"]


def get_bm_orders_from_marketplace(BMInstance: BackMarketClient, orderIDs: List[str]) -> List[Dict]:
    return [BMInstance.getOrderByID(orderID=order_id) for order_id in orderIDs]


def get_rf_orders_from_marketplace(RFInstance: RefurbedClient, orderIDs: List[str]) -> List[Dict]:
    return [RFInstance.getOrderByID(orderID=order_id) for order_id in orderIDs]


def get_update_data_from_orders(new_orders: List[Dict], api_instance: MarketPlaceClient,
                                googleSheetIDS: Dict[str, int]) -> \
        List[Dict[str, Dict | int]]:
    ordersToBeUpdated = []
    for order in new_orders:
        formattedOrderList = api_instance.convertOrderToSheetColumns(order)
        for item in order[api_instance.itemKeyName]:
            primaryKey = f"{order[api_instance.orderIDFieldName]}_{item['id']}"
            if primaryKey not in googleSheetIDS:
                continue
            for formattedOrder in formattedOrderList:
                if f"{formattedOrder['order_id']}_{formattedOrder['item_id']}" == primaryKey:
                    ordersToBeUpdated.append({"data": formattedOrder,
                                              "row": googleSheetIDS[primaryKey]})
    return ordersToBeUpdated


def update_sheet_with_new_orders(rf_orders, bm_orders, RFAPIInstance, BMAPIInstance, service):
    googleSheetOrderIDs = service.getEntireColumnData(sheetID=SPREADSHEET_ID, sheetName=SPREADSHEET_NAME,
                                                      column="A")

    googleSheetItemIDs = service.getEntireColumnData(sheetID=SPREADSHEET_ID,
                                                     sheetName=SPREADSHEET_NAME,
                                                     column="AQ")

    googleSheetIDS = {f"{item[0][0]}_{item[1][0]}": idx + 1 for idx, item in
                      enumerate(list(zip(googleSheetOrderIDs[1:], googleSheetItemIDs[1:]))) if
                      (len(item) > 1 and len(item[0]) > 0 and len(item[1]) > 0)}

    ordersToBeUpdated = {
        "BackMarket": [],
        "Refurbed": []
    }

    ordersToBeUpdated["Refurbed"] += get_update_data_from_orders(rf_orders, RFAPIInstance, googleSheetIDS)
    ordersToBeUpdated["BackMarket"] += get_update_data_from_orders(bm_orders, BMAPIInstance, googleSheetIDS)

    # contains flattened order list to upload to sheets
    flattenedOrderList = []
    flattenedRowNumberList = []
    flattenedOrderList += [[CellData(value=val, field_type=FieldType.normal, field_values=[])
                            for val in d["data"].values()] for d in
                           ordersToBeUpdated["BackMarket"] + ordersToBeUpdated["Refurbed"]]
    flattenedRowNumberList += [d["row"] for d in ordersToBeUpdated["BackMarket"] + ordersToBeUpdated["Refurbed"]]
    if flattenedOrderList:
        service.updateEntireRowValuesFromRowNumber(sheetTitle=SPREADSHEET_NAME,
                                                   documentID=SPREADSHEET_ID,
                                                   dataList=flattenedOrderList,
                                                   rowNumberList=flattenedRowNumberList)
    return flattenedOrderList


def performAddNewOrdersUpdate(service: GoogleSheetsService, BMAPIInstance: BackMarketClient,
                              RFAPIInstance: RefurbedClient, days: int, single_order_id: Optional[str],
                              single_order_id_vendor: Optional[str]):
    """
    Appends new orders to the bottom of the sheet
    :param service: SheetsService
    :param BMAPIInstance: BackMarketClient
    :param RFAPIInstance: RefurbedClient
    :param days: Number of days back from today to pull the new records for
    :param single_order_id: Adds this particular order id: If this is set to not None, all other params are ignored
    :param single_order_id_vendor: Vendor for single order id
    :return:
    """
    googleSheetOrderIDs = service.getEntireColumnData(sheetID=SPREADSHEET_ID, sheetName=SPREADSHEET_NAME,
                                                      column="A")
    googleSheetOrderIDs = {item[0] for item in googleSheetOrderIDs[1:] if len(item) > 0}

    nowDateTime = datetime.datetime.now()
    RFNewOrders = []
    BMnewOrders = []
    if not single_order_id:
        RFNewOrders = RFAPIInstance.getOrdersBetweenDates(start=nowDateTime - datetime.timedelta(days), end=nowDateTime)
        BMnewOrders = BMAPIInstance.getOrdersBetweenDates(start=nowDateTime - datetime.timedelta(days), end=nowDateTime)

    else:
        if single_order_id_vendor == "Backmarket":
            BMnewOrders.append(BMAPIInstance.getOrderByID(orderID=single_order_id, normalizeFields=True))
        elif single_order_id_vendor == "Refurbed":
            RFNewOrders.append(RFAPIInstance.getOrderByID(orderID=single_order_id))

    ordersToBeAdded = {
        "BackMarket": [],
        "Refurbed": []
    }

    for order in RFNewOrders:
        if str(order["id"]) not in googleSheetOrderIDs:
            ordersToBeAdded["Refurbed"] += RFAPIInstance.convertOrderToSheetColumns(order)

    for order in BMnewOrders:
        if str(order["order_id"]) not in googleSheetOrderIDs:
            ordersToBeAdded["BackMarket"] += BMAPIInstance.convertOrderToSheetColumns(order)

    """
    Step 1 is to flatten everything except the orderlines
    """
    # contains flattened order list to upload to sheets
    flattenedOrderList = []

    flattenedOrderList += [list(d.values()) for d in ordersToBeAdded["Refurbed"] + ordersToBeAdded["BackMarket"]]
    if flattenedOrderList:
        service.appendValuesToBottomOfSheet(data=flattenedOrderList, sheetTitle=SPREADSHEET_NAME,
                                            documentID=SPREADSHEET_ID)
    return len(flattenedOrderList)


def performUpdateExistingOrdersUpdate(service: GoogleSheetsService, BMAPIInstance: BackMarketClient,
                                      RFAPIInstance: RefurbedClient):
    """
    Updates details orders that were placed in the last 2 days
    :param service: SheetsService
    :param BMAPIInstance: BackMarketClient
    :param RFAPIInstance: RefurbedClient
    :return:
    """
    # check for updates from the last two days
    nowDateTime = datetime.datetime.now()
    RFNewOrders = RFAPIInstance.getOrdersBetweenDates(start=nowDateTime - datetime.timedelta(2), end=nowDateTime)
    BMnewOrders = BMAPIInstance.getOrdersBetweenDates(start=nowDateTime - datetime.timedelta(2), end=nowDateTime)

    return update_sheet_with_new_orders(RFNewOrders, BMnewOrders, RFAPIInstance, BMAPIInstance, service)


def batchUpdateGoogleSheetWithOrderIDs():
    try:
        key = request.headers.get('auth-token')

        if not key or key != APP_AUTH_TOKEN:
            raise IncorrectAuthTokenException("Incorrect auth token provided")

        service = GoogleSheetsService()
        RFAPIInstance = RefurbedClient()
        BMAPIInstance = BackMarketClient()

        body = request.get_json()
        rf_orderIDs = body["rf_orders"]
        bm_orderIDs = body["bm_orders"]
        # if each of these are above length 10, raise exception
        if len(rf_orderIDs) > 10 or len(bm_orderIDs) > 10:
            raise ResourceExhaustedException('Keep orders under 10 per marketplace in each request!')

        rf_orders = get_rf_orders_from_marketplace(RFAPIInstance, rf_orderIDs)
        bm_orders = get_bm_orders_from_marketplace(BMAPIInstance, bm_orderIDs)

        update_sheet_with_new_orders(rf_orders, bm_orders, RFAPIInstance, BMAPIInstance, service)

        return make_response(jsonify({"type": "success",
                                      "message": f"Updated RF: {len(rf_orderIDs)}, BM: {len(bm_orderIDs)}"
                                      }),
                             HTTP_200_OK)

    except KeyError:
        return make_response(jsonify({"type": "fail",
                                      "message": "Key `rf_orders` or `bm_orders` not in body"
                                      }),
                             HTTP_400_BAD_REQUEST)

    except ResourceExhaustedException as e:
        return make_response(jsonify({"type": "fail",
                                      "message": e.args[0]
                                      }),
                             HTTP_400_BAD_REQUEST)
    except HTTPExceptions.BadRequest as e:
        return make_response(jsonify({"type": "Bad Request",
                                      "message": "No JSON body in request"
                                      }),
                             HTTP_400_BAD_REQUEST)
    except IncorrectAuthTokenException as e:
        return make_response(jsonify({"type": "fail",
                                      "message": e.args[0]
                                      }),
                             HTTP_401_UNAUTHORIZED)
    except Exception:
        print(traceback.print_exc())
        return make_response(jsonify({"type": "fail",
                                      "message": "Contact support. Check server logs"
                                      }),
                             HTTP_500_INTERNAL_SERVER_ERROR)


def updateGoogleSheet():
    try:
        key = request.headers.get('auth-token')

        if not key or key != APP_AUTH_TOKEN:
            raise IncorrectAuthTokenException("Incorrect auth token provided")

        start = time.time()
        service = GoogleSheetsService()
        RFAPIInstance = RefurbedClient()
        BMAPIInstance = BackMarketClient()

        body = request.get_json()
        numberOfDaysToUpdate = body["days"] if "days" in body else 0

        if "single_order_id" in body:
            recordsUpdated = 1
            newRecordsAdded = performAddNewOrdersUpdate(service=service,
                                                        BMAPIInstance=BMAPIInstance,
                                                        RFAPIInstance=RFAPIInstance,
                                                        days=numberOfDaysToUpdate,
                                                        single_order_id=body["single_order_id"],
                                                        single_order_id_vendor=body["vendor"])
        else:

            recordsUpdated = performUpdateExistingOrdersUpdate(service=service,
                                                               BMAPIInstance=BMAPIInstance,
                                                               RFAPIInstance=RFAPIInstance)
            newRecordsAdded = performAddNewOrdersUpdate(service=service,
                                                        BMAPIInstance=BMAPIInstance,
                                                        RFAPIInstance=RFAPIInstance,
                                                        days=numberOfDaysToUpdate,
                                                        single_order_id=None,
                                                        single_order_id_vendor=None)

        end = time.time()

        print(f"Time taken to handle this request {end - start}")

        return make_response(jsonify({"type": "success",
                                      "message": f"Added {newRecordsAdded} records! Updated {len(recordsUpdated)} records!"
                                      }),
                             200)
    except GenericAPIException:
        return make_response(jsonify({"type": "fail",
                                      "message": "Order id not found in marketplace"
                                      }),
                             400)
    except googleapiclient.errors.HttpError as e:
        return make_response(jsonify({"type": "Google API fail",
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
