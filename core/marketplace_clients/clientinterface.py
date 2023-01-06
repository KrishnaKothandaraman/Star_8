import datetime
from typing import List
from core.marketplace_clients.databaseutils.column_mapping import columnMapping


class MarketPlaceClient:
    key: str
    vendor: str
    dateFieldName: str
    dateStringFormat: str
    itemKeyName: str

    def __init__(self, key):
        self.key = key
        self.vendor = ""
        self.dateFieldName = ""
        self.dateStringFormat = ""
        self.itemKeyName = ""

    @staticmethod
    def getValueFromColumnMapping(col, order: dict):
        """Expects col of 3 types
            1. Int value -> returns col back. Signifies constant value for column
            2. String value of type level1/level2/level3 to specify keys of different levels in the dictionary
            3. None value -> returns empty string
        """
        if type(col) == int:
            return col

        if not col:
            return ""

        multiLevelCol = col.split('/')
        val = order
        for level in multiLevelCol:
            val = val.get(level, "")
        return val

    @staticmethod
    def convertDateTimeToString(dt: datetime.datetime, timeStr: str):
        return f"{dt.strftime('%Y-%m-%d')} {timeStr}"

    @staticmethod
    def convertBetweenDateTimeStringFormats(inputString: str, inputFormat: str, outputFormat: str) -> str:
        return datetime.datetime.strptime(inputString, inputFormat).strftime(outputFormat)

    """
        # for each order that may contain multiple orderlines
        for order in ordersToBeAdded:
            # add supplement address field to clean code to clean code
            order["shipping_address"].setdefault("supplement", "")
            order["invoice_address"].setdefault("supplement", "")
            order["invoice_address"].setdefault("company_vatin", "")

            order["shipping_address"].pop("company_name", None)
            order["invoice_address"].pop("company_name",None)

            # for each orderline in an order
            for i, _ in enumerate(order["items"]):
                # create a row
                singleFlatOrder = []
                for key, item in order.items():
                    if key != "items":
                        if type(item) != dict:
                            item = convertBetweenDateTimeStringFormats(item, "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d %H:%M:%S") if key == "released_at" else item
                            singleFlatOrder.append(str(item))
                        else:
                            singleFlatOrder += [str(val) for _, val in item.items()]
                    # only add the current ith orderline to this row
                    else:
                        singleFlatOrder += [val for _, val in order["items"][i].items()]
                flattenedOrderList.append(singleFlatOrder)
    """

    def convertOrdersToSheetColumns(self, orders: List[dict]):
        formattedOrdersList = []
        for order in orders:
            for i, _ in enumerate(order[self.itemKeyName]):
                formattedOrder = {}
                for col, mapping in columnMapping["global"].items():
                    formattedOrder[col] = self.getValueFromColumnMapping(mapping[self.vendor], order)
                    if mapping[self.vendor] == self.dateFieldName:
                        formattedOrder[col] = self.convertBetweenDateTimeStringFormats(formattedOrder[col], self.dateStringFormat, "%Y-%m-%d %H:%M:%S")
                for col, mapping in columnMapping["items"].items():
                    formattedOrder[col] = self.getValueFromColumnMapping(mapping[self.vendor],
                                                                         order[self.itemKeyName][i])
                formattedOrdersList.append(formattedOrder)
        return formattedOrdersList
