import datetime
import os

import werkzeug

from core.custom_exceptions.general_exceptions import IncorrectAuthTokenException
from core.custom_exceptions.google_service_exceptions import IncorrectSheetTitleException
import time
import traceback
import werkzeug.exceptions as HTTPExceptions
import googleapiclient.errors
from flask import request, make_response, jsonify
from core.google_services.googleSheetsService import GoogleSheetsService
from core.marketplace_clients.bmclient import BackMarketClient
from core.marketplace_clients.rfclient import RefurbedClient

GOOGLE_DOCS_MIMETYPE = "application/vnd.google-apps.document"
GOOGLE_SHEETS_MIMETYPE = "application/vnd.google-apps.spreadsheet"
SPREADSHEET_ID = "19OXMfru14WMEI4nja9SCAljnCDrHlw33SHLO77vAmVo"
SPREADSHEET_NAME = "Combined_Orders"

APP_AUTH_TOKEN = os.environ["APPAUTHTOKEN"]


def performAddNewOrdersUpdate(service: GoogleSheetsService, BMAPIInstance: BackMarketClient,
                              RFAPIInstance: RefurbedClient, days: int):
    """
    Appends new orders to the bottom of the sheet
    :param service: SheetsService
    :param BMAPIInstance: MarketPlaceClient
    :param RFAPIInstance: MarketPlaceClient
    :param days: Number of days back from today to pull the new records for
    :return:
    """
    googleSheetOrderIDs = service.getEntireColumnData(sheetID=SPREADSHEET_ID, sheetName=SPREADSHEET_NAME,
                                                      column="A")
    googleSheetOrderIDs = {item[0] for item in googleSheetOrderIDs[1:] if len(item) > 0}

    nowDateTime = datetime.datetime.now()
    RFNewOrders = RFAPIInstance.getOrdersBetweenDates(start=nowDateTime - datetime.timedelta(days), end=nowDateTime)
    BMnewOrders = BMAPIInstance.getOrdersBetweenDates(start=nowDateTime - datetime.timedelta(days), end=nowDateTime)

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

    service.appendValuesToBottomOfSheet(data=flattenedOrderList, sheetTitle=SPREADSHEET_NAME,
                                        documentID=SPREADSHEET_ID)
    return len(flattenedOrderList)


def performUpdateExistingOrdersUpdate(service: GoogleSheetsService, BMAPIInstance: BackMarketClient,
                                      RFAPIInstance: RefurbedClient):
    """
    Updates details orders that were placed in the last 2 days
    :param service: SheetsService
    :param BMAPIInstance: MarketPlaceClient
    :param RFAPIInstance: MarketPlaceClient
    :return:
    """
    googleSheetOrderIDs = service.getEntireColumnData(sheetID=SPREADSHEET_ID, sheetName=SPREADSHEET_NAME,
                                                      column="A")

    googleSheetItemIDs = service.getEntireColumnData(sheetID=SPREADSHEET_ID,
                                                     sheetName=SPREADSHEET_NAME,
                                                     column="AP")

    googleSheetIDS = {f"{item[0][0]}_{item[1][0]}": idx + 1 for idx, item in
                      enumerate(list(zip(googleSheetOrderIDs[1:], googleSheetItemIDs[1:]))) if
                      (len(item) > 1 and len(item[0]) > 0 and len(item[1]) > 0)}

    # check for updates from the last two days
    nowDateTime = datetime.datetime.now()
    RFNewOrders = RFAPIInstance.getOrdersBetweenDates(start=nowDateTime - datetime.timedelta(2), end=nowDateTime)
    BMnewOrders = BMAPIInstance.getOrdersBetweenDates(start=nowDateTime - datetime.timedelta(2), end=nowDateTime)
    ordersToBeUpdated = {
        "BackMarket": [],
        "Refurbed": []
    }

    for order in RFNewOrders:
        formattedOrderList = RFAPIInstance.convertOrderToSheetColumns(order)
        for item in order["items"]:
            primaryKey = f"{order['id']}_{item['id']}"
            if primaryKey not in googleSheetIDS:
                continue
            for formattedOrder in formattedOrderList:
                if f"{formattedOrder['order_id']}_{formattedOrder['item_id']}" == primaryKey:
                    ordersToBeUpdated["Refurbed"].append({"data": formattedOrder,
                                                          "row": googleSheetIDS[primaryKey]})

    for order in BMnewOrders:
        formattedOrderList = BMAPIInstance.convertOrderToSheetColumns(order)
        for item in order["orderlines"]:
            primaryKey = f"{order['order_id']}_{item['id']}"
            if primaryKey not in googleSheetIDS:
                continue
            for formattedOrder in formattedOrderList:
                if f"{formattedOrder['order_id']}_{formattedOrder['item_id']}" == primaryKey:
                    ordersToBeUpdated["Refurbed"].append({"data": formattedOrder,
                                                          "row": googleSheetIDS[primaryKey]})

    # contains flattened order list to upload to sheets
    flattenedOrderList = []
    flattenedRowNumberList = []
    flattenedOrderList += [list(d["data"].values()) for d in
                           ordersToBeUpdated["BackMarket"] + ordersToBeUpdated["Refurbed"]]
    flattenedRowNumberList += [d["row"] for d in ordersToBeUpdated["BackMarket"] + ordersToBeUpdated["Refurbed"]]

    service.updateEntireRowValuesFromRowNumber(sheetTitle=SPREADSHEET_NAME,
                                               documentID=SPREADSHEET_ID,
                                               dataList=flattenedOrderList,
                                               rowNumberList=flattenedRowNumberList)

    return len(flattenedOrderList)


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

        recordsUpdated = performUpdateExistingOrdersUpdate(service=service,
                                                           BMAPIInstance=BMAPIInstance,
                                                           RFAPIInstance=RFAPIInstance)
        newRecordsAdded = performAddNewOrdersUpdate(service=service,
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

# service = GoogleSheetsService()
# RFAPIInstance = RefurbedClient(key=keys["RF"]["token"], itemKeyName="items",
#                                dateFieldName="released_at", dateStringFormat="%Y-%m-%dT%H:%M:%S.%fZ")
# BMAPIInstance = BackMarketClient(key=keys["BM"]["token"], itemKeyName="orderlines",
#                                  dateFieldName="date_creation", dateStringFormat="%Y-%m-%dT%H:%M:%S%z")
# #print(performAddNewOrdersUpdate(service, BMAPIInstance=BMAPIInstance, RFAPIInstance=RFAPIInstance))
# print(updateGoogleSheetNonApi())
#
# def updateGoogleSheetNonApi():
#     start = time.time()
#     try:
#         service = GoogleSheetsService()
#     except Exception as e:
#         print(traceback.print_exc())
#         return
#         # return make_response(jsonify({"type": "fail",
#         #                               "message": "Failed to open Google Sheets. Check server logs for more info"
#         #                               }),
#         #                      400)
#
#     googleSheetOrderIDs = service.getEntireColumnData(sheetID=SPREADSHEET_ID, sheetName=SPREADSHEET_NAME,
#                                                       column="A")
#     googleSheetOrderIDs = {item[0] for item in googleSheetOrderIDs[1:] if len(item) > 0}
#
#     RFAPIInstance = RefurbedClient()
#     BMAPIInstance = BackMarketClient()
#
#     offset = 20
#     startOffset = 20
#     endOffset = 0
#
#     for i in range(0, 35):
#         startDatetime = datetime.datetime.now() - datetime.timedelta(days=startOffset + (i * offset))
#         nowDateTime = datetime.datetime.now() - datetime.timedelta(days=endOffset + (i * offset))
#         RFNewOrders = RFAPIInstance.getOrdersBetweenDates(start=startDatetime, end=nowDateTime)
#         BMnewOrders = BMAPIInstance.getOrdersBetweenDates(start=startDatetime, end=nowDateTime)
#
#         ordersToBeAdded = {
#             "BackMarket": [],
#             "Refurbed": []
#         }
#
#         for order in RFNewOrders:
#             if str(order["id"]) not in googleSheetOrderIDs:
#                 ordersToBeAdded["Refurbed"].append(order)
#
#         for order in BMnewOrders:
#             if str(order["order_id"]) not in googleSheetOrderIDs:
#                 ordersToBeAdded["BackMarket"].append(order)
#
#         """
#         Step 1 is to flatten everything except the orderlines
#         """
#         # contains flattened order list to upload to sheets
#         flattenedOrderList = []
#
#         convertedBMOrders = BMAPIInstance.convertOrdersToSheetColumns(ordersToBeAdded["BackMarket"])
#         convertedRFOrders = RFAPIInstance.convertOrdersToSheetColumns(ordersToBeAdded["Refurbed"])
#
#         flattenedOrderList += [list(d.values()) for d in convertedRFOrders + convertedBMOrders]
#
#         service.appendValuesToBottomOfSheet(data=flattenedOrderList, sheetTitle=SPREADSHEET_NAME,
#                                             documentID=SPREADSHEET_ID)
#         end = time.time()
#
#         print(f"Time taken to handle this request between {startOffset=}, {endOffset=}: {end - start}")