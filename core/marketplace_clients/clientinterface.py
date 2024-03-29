import datetime
from typing import List, Literal, Optional

import requests

from core.marketplace_clients.databaseutils.column_mapping import columnMapping
import core.types.refurbedAPI as RFTypes
from core.types.orderStateTypes import newStates

class MarketPlaceClient:
    key: str
    vendor: str
    dateFieldName: str
    dateStringFormat: str
    itemKeyName: str
    skuFieldName: str
    orderIDFieldName: str

    def __init__(self):
        self.key = ""
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
        if not col:
            return "-"

        # constant value. Return str in between <>
        if col[0] == "<" and col[-1] == ">":
            return col[1:-1]

        multiLevelCol = col.split('/')
        val = order
        for i, level in enumerate(multiLevelCol):
            # last level. There could be column joining through + operation
            if i == len(multiLevelCol) - 1 and len(level.split("+")) > 1:
                joinedVal = ""
                for col in level.split("+"):
                    joinedVal += str(val.get(col))
                val = joinedVal
            else:
                # global column in item array
                if level == "..":
                    continue
                val = val.get(level, "")

        if val is None:
            val = ""

        return val

    @staticmethod
    def convertDateTimeToString(dt: datetime.datetime, timeStr: str):
        return f"{dt.strftime('%Y-%m-%d')}{timeStr}"

    @staticmethod
    def convertBetweenDateTimeStringFormats(inputString: str, inputFormat: str, outputFormat: str) -> str:
        return datetime.datetime.strptime(inputString, inputFormat).strftime(outputFormat)

    def convertOrderToSheetColumns(self, order: dict) -> List[dict]:
        formattedOrders = []
        for i, _ in enumerate(order[self.itemKeyName]):
            formattedOrder = {}
            for col, mapping in columnMapping["global"].items():
                formattedOrder[col] = self.getValueFromColumnMapping(mapping[self.vendor], order)
                if mapping[self.vendor] == self.dateFieldName:
                    formattedOrder[col] = self.convertBetweenDateTimeStringFormats(formattedOrder[col],
                                                                                   self.dateStringFormat,
                                                                                   "%Y-%m-%d %H:%M:%S")
            for col, mapping in columnMapping["items"].items():

                if self.__checkIfGlobalMappingInItemMapping(mapping[self.vendor]):
                    formattedOrder[col] = self.getValueFromColumnMapping(mapping[self.vendor],
                                                                         order)
                else:
                    formattedOrder[col] = self.getValueFromColumnMapping(mapping[self.vendor],
                                                                         order[self.itemKeyName][i])
                if self.vendor == "Refurbed" and col == "shipper":
                    formattedOrder[col] = RFTypes.ShippingProfileIDMapping[str(formattedOrder[col])]

            formattedOrders.append(formattedOrder)

        return formattedOrders

    def getOrderItems(self, order):
        return order[self.itemKeyName]

    def getSku(self, orderItem):
        return orderItem[self.skuFieldName]

    def getOrderID(self, order):
        return order[self.orderIDFieldName]

    def updateStateOfOrder(self, order, state: newStates, body: Optional[dict]):
        raise NotImplementedError

    def MakeUpdateOrderStateByOrderIDRequest(self, orderID, body) -> requests.Response:
        raise NotImplementedError

    @staticmethod
    def __getMarketPlaceState(state: newStates):
        raise NotImplementedError

    @staticmethod
    def generateItemsBodyForSWDCreateOrderRequest(orderItems: List[dict], swdModelName: List[str]) -> List[dict]:
        raise NotImplementedError

    @staticmethod
    def __checkIfGlobalMappingInItemMapping(mapping: str):
        return mapping and len(mapping) > 2 and mapping[:3] == "../"

    @staticmethod
    def getBodyForUpdateStateToShippedRequest(shipping_data) -> dict:
        raise NotImplementedError

    def updateSkuOfOrder(self, order, old_sku, new_sku):
        for order_line in order[self.itemKeyName]:
            if order_line[self.skuFieldName] == old_sku:
                order_line[self.skuFieldName] = new_sku
                break
        return order
