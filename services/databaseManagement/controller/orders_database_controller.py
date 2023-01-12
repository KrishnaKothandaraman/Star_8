import datetime
import time
import traceback
from core.google_services.googleSheetsService import GoogleSheetsService
from core.marketplace_clients.bmclient import BackMarketClient
from core.marketplace_clients.rfclient import RefurbedClient
from get_order_history import keys

GOOGLE_DOCS_MIMETYPE = "application/vnd.google-apps.document"
GOOGLE_SHEETS_MIMETYPE = "application/vnd.google-apps.spreadsheet"
SPREADSHEET_ID = "19OXMfru14WMEI4nja9SCAljnCDrHlw33SHLO77vAmVo"
SPREADSHEET_NAME = "Combined_Orders"


def performAddNewOrdersUpdate(service, BMAPIInstance: BackMarketClient, RFAPIInstance: RefurbedClient):
    """
    Appends new orders to the bottom of the sheet
    :param service: SheetsService
    :param BMAPIInstance: MarketPlaceClient
    :param RFAPIInstance: MarketPlaceClient
    :return:
    """
    googleSheetOrderIDs = service.getEntireColumnData(sheetID=SPREADSHEET_ID, sheetName=SPREADSHEET_NAME,
                                                      column="A")
    googleSheetOrderIDs = {item[0] for item in googleSheetOrderIDs[1:] if len(item) > 0}

    nowDateTime = datetime.datetime.now()
    RFNewOrders = RFAPIInstance.getOrdersBetweenDates(start=nowDateTime, end=nowDateTime)
    BMnewOrders = BMAPIInstance.getOrdersBetweenDates(start=nowDateTime, end=nowDateTime)

    ordersToBeAdded = {
        "BackMarket": [],
        "Refurbed": []
    }

    for order in RFNewOrders:
        if str(order["id"]) not in googleSheetOrderIDs:
            ordersToBeAdded["Refurbed"].append(order)

    for order in BMnewOrders:
        if str(order["order_id"]) not in googleSheetOrderIDs:
            ordersToBeAdded["BackMarket"].append(order)

    """
    Step 1 is to flatten everything except the orderlines
    """
    # contains flattened order list to upload to sheets
    flattenedOrderList = []

    convertedBMOrders = BMAPIInstance.convertOrdersToSheetColumns(ordersToBeAdded["BackMarket"])
    convertedRFOrders = RFAPIInstance.convertOrdersToSheetColumns(ordersToBeAdded["Refurbed"])

    flattenedOrderList += [list(d.values()) for d in convertedRFOrders + convertedBMOrders]

    service.appendValuesToBottomOfSheet(data=flattenedOrderList, sheetTitle=SPREADSHEET_NAME,
                                        documentID=SPREADSHEET_ID)
    return len(flattenedOrderList)


def performUpdateExistingOrdersUpdate(service: GoogleSheetsService, BMAPIInstance, RFAPIInstance):
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
                                                     column="AQ")

    googleSheetIDS = {f"{item[0][0]}_{item[1][0]}": idx + 1 for idx, item in enumerate(list(zip(googleSheetOrderIDs[1:], googleSheetItemIDs[1:]))) if len(item) > 0}

    # check for updates from the last two days
    nowDateTime = datetime.datetime.now()
    RFNewOrders = RFAPIInstance.getOrdersBetweenDates(start=nowDateTime - datetime.timedelta(2), end=nowDateTime)
    BMnewOrders = BMAPIInstance.getOrdersBetweenDates(start=nowDateTime - datetime.timedelta(2), end=nowDateTime)

    ordersToBeUpdated = {
        "BackMarket": [],
        "Refurbed": []
    }

    for order in RFNewOrders:
        for item in order["items"]:
            primaryKey = f"{order['id']}_{item['id']}"
            if primaryKey in googleSheetIDS:
                ordersToBeUpdated["Refurbed"].append({"data": order, "row": googleSheetIDS[primaryKey]})

    for order in BMnewOrders:
        for item in order["orderlines"]:
            primaryKey = f"{order['order_id']}_{item['id']}"
            if primaryKey in googleSheetIDS:
                ordersToBeUpdated["BackMarket"].append({"data": order, "row": googleSheetIDS[primaryKey]})

    # contains flattened order list to upload to sheets
    flattenedOrderList = []

    convertedBMOrders = BMAPIInstance.convertOrdersToSheetColumns(
        [order["data"] for order in ordersToBeUpdated["BackMarket"]])
    convertedRFOrders = RFAPIInstance.convertOrdersToSheetColumns(
        [order["data"] for order in ordersToBeUpdated["Refurbed"]])

    flattenedOrderList += [list(d.values()) for d in convertedRFOrders + convertedBMOrders]
    flattenedRowNumberList = [row["row"] for row in (ordersToBeUpdated["Refurbed"] + ordersToBeUpdated["BackMarket"])]

    service.updateEntireRowValuesFromRowNumber(sheetTitle=SPREADSHEET_NAME,
                                               documentID=SPREADSHEET_ID,
                                               dataList=flattenedOrderList,
                                               rowNumberList=flattenedRowNumberList)

    return len(flattenedOrderList)


def updateGoogleSheetNonApi():
    start = time.time()
    try:
        service = GoogleSheetsService()
    except Exception as e:
        print(traceback.print_exc())
        return
        # return make_response(jsonify({"type": "fail",
        #                               "message": "Failed to open Google Sheets. Check server logs for more info"
        #                               }),
        #                      400)

    googleSheetOrderIDs = service.getEntireColumnData(sheetID=SPREADSHEET_ID, sheetName=SPREADSHEET_NAME,
                                                      column="A")
    googleSheetOrderIDs = {item[0] for item in googleSheetOrderIDs[1:] if len(item) > 0}

    RFAPIInstance = RefurbedClient(key=keys["RF"]["token"], itemKeyName="items",
                                   dateFieldName="released_at", dateStringFormat="%Y-%m-%dT%H:%M:%S.%fZ")
    BMAPIInstance = BackMarketClient(key=keys["BM"]["token"], itemKeyName="orderlines",
                                     dateFieldName="date_creation", dateStringFormat="%Y-%m-%dT%H:%M:%S%z")

    offset = 20
    startOffset = 20
    endOffset = 0

    for i in range(0, 35):
        startDatetime = datetime.datetime.now() - datetime.timedelta(days=startOffset + (i * offset))
        nowDateTime = datetime.datetime.now() - datetime.timedelta(days=endOffset + (i * offset))
        RFNewOrders = RFAPIInstance.getOrdersBetweenDates(start=startDatetime, end=nowDateTime)
        BMnewOrders = BMAPIInstance.getOrdersBetweenDates(start=startDatetime, end=nowDateTime)

        ordersToBeAdded = {
            "BackMarket": [],
            "Refurbed": []
        }

        for order in RFNewOrders:
            if str(order["id"]) not in googleSheetOrderIDs:
                ordersToBeAdded["Refurbed"].append(order)

        for order in BMnewOrders:
            if str(order["order_id"]) not in googleSheetOrderIDs:
                ordersToBeAdded["BackMarket"].append(order)

        """
        Step 1 is to flatten everything except the orderlines
        """
        # contains flattened order list to upload to sheets
        flattenedOrderList = []

        convertedBMOrders = BMAPIInstance.convertOrdersToSheetColumns(ordersToBeAdded["BackMarket"])
        convertedRFOrders = RFAPIInstance.convertOrdersToSheetColumns(ordersToBeAdded["Refurbed"])

        flattenedOrderList += [list(d.values()) for d in convertedRFOrders + convertedBMOrders]

        service.appendValuesToBottomOfSheet(data=flattenedOrderList, sheetTitle=SPREADSHEET_NAME,
                                            documentID=SPREADSHEET_ID)
        end = time.time()

        print(f"Time taken to handle this request between {startOffset=}, {endOffset=}: {end - start}")


# service = GoogleSheetsService()
# RFAPIInstance = RefurbedClient(key=keys["RF"]["token"], itemKeyName="items",
#                                dateFieldName="released_at", dateStringFormat="%Y-%m-%dT%H:%M:%S.%fZ")
# BMAPIInstance = BackMarketClient(key=keys["BM"]["token"], itemKeyName="orderlines",
#                                  dateFieldName="date_creation", dateStringFormat="%Y-%m-%dT%H:%M:%S%z")
# #print(performAddNewOrdersUpdate(service, BMAPIInstance=BMAPIInstance, RFAPIInstance=RFAPIInstance))
# print(updateGoogleSheetNonApi())
