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
SPREADSHEET_NAME = "tester"


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

    for i in range(16, 35):
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


def performAddNewOrdersUpdate(service):

    googleSheetOrderIDs = service.getEntireColumnData(sheetID=SPREADSHEET_ID, sheetName=SPREADSHEET_NAME,
                                                      column="A")
    googleSheetOrderIDs = {item[0] for item in googleSheetOrderIDs[1:] if len(item) > 0}

    RFAPIInstance = RefurbedClient(key=keys["RF"]["token"], itemKeyName="items",
                                   dateFieldName="released_at", dateStringFormat="%Y-%m-%dT%H:%M:%S.%fZ")
    BMAPIInstance = BackMarketClient(key=keys["BM"]["token"], itemKeyName="orderlines",
                                     dateFieldName="date_creation", dateStringFormat="%Y-%m-%dT%H:%M:%S%z")
    nowDateTime = datetime.datetime.now()
    RFNewOrders = RFAPIInstance.getOrdersBetweenDates(start=nowDateTime - datetime.timedelta(days=4), end=nowDateTime)
    BMnewOrders = BMAPIInstance.getOrdersBetweenDates(start=nowDateTime - datetime.timedelta(days=4), end=nowDateTime)

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