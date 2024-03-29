import dataclasses
import enum
import json

from core.custom_exceptions.google_service_exceptions import IncorrectSheetTitleException
import io
from typing import List, Dict, Tuple
import apiclient
from googleapiclient.http import MediaIoBaseDownload
from core.config.googleServiceConfiguration import GOOGLE_DRIVE_SERVICE_NAME, GOOGLE_SHEETS_SERVICE_NAME
from core.google_services.googleAppServiceFactory import GoogleAppServiceFactory

GOOGLE_SHEETS_STARTING_CELL = "A15"

"""
Docs: https://googleapis.github.io/google-api-python-client/docs/dyn/sheets_v4.spreadsheets.html#getByDataFilter
"""


class FieldType(enum.Enum):
    normal = enum.auto()
    dropdown = enum.auto()


@dataclasses.dataclass
class CellData:
    value: str
    field_type: FieldType
    field_values: List[str]

    def __init__(self, value, field_type, field_values):
        self.value = value
        self.field_type = field_type
        self.field_values = field_values


class GoogleSheetsService:
    def __init__(self):
        self.driveService = GoogleAppServiceFactory.getGoogleAppService(GOOGLE_DRIVE_SERVICE_NAME)
        self.sheetsService: apiclient.module.discovery.Resource = GoogleAppServiceFactory.getGoogleAppService(
            GOOGLE_SHEETS_SERVICE_NAME)

    def generateCopyFromTemplate(self, templateFileId, documentName='Document'):
        body = {'name': documentName}
        return self.driveService.files().copy(body=body, fileId=templateFileId,
                                              fields='id').execute().get('id')

    def getFileMetaData(self, fileId: str):
        return self.driveService.files().get(fileId=fileId).execute()

    def downloadDocument(self, fileId):
        downloadRequest = self.driveService.files().export_media(
            fileId=fileId, mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        fileHandler = io.BytesIO()
        downloader = MediaIoBaseDownload(fileHandler, downloadRequest)
        done = False

        while done is False:
            status, done = downloader.next_chunk()

        fileHandler.seek(0)
        return fileHandler.read()

    def createTableFromOrders(self, documentID, orders: List[Dict]):

        spreadsheet = self.sheetsService.spreadsheets().get(spreadsheetId=documentID).execute()
        # use id of first sheet
        sheet_id = spreadsheet["sheets"][0]["properties"]["sheetId"]

        requests = [{
            "insertDimension": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "ROWS",
                    "startIndex": 15,
                    "endIndex": 15 + len(orders) - 1
                },
                "inheritFromBefore": True
            }
        }]

        # add empty rows
        self.executeBatchRequest(requests=requests, documentId=documentID)

        # add row data
        values = [[val for val in order.values()] for order in orders]
        body = {
            'values': values
        }
        result = self.sheetsService.spreadsheets().values().update(
            spreadsheetId=documentID, range=GOOGLE_SHEETS_STARTING_CELL,
            valueInputOption="USER_ENTERED", body=body).execute()
        print(f"{result.get('updatedCells')} cells updated.")

        return True

    @staticmethod
    def makeReplaceTextRequests(data={}, matchCase=True):
        context = data.items()
        requests = [{
            'findReplace': {
                'find': '{{%s}}' % key.upper(),
                'replacement': value,
                'matchCase': matchCase,
                "allSheets": True
            }} for key, value in context]

        return requests

    @staticmethod
    def makeReplaceImageRequests(data={}):
        context = data.iteritems() if hasattr({}, 'iteritems') else data.items()
        requests = [{'replaceImage': {
            'imageObjectId': key,
            'uri': value,
            'imageReplaceMethod': 'CENTER_CROP'
        }} for key, value in context]

        return requests

    @staticmethod
    def getValueAsString(val):
        if type(val) == int:
            return str(val)

        elif isinstance(val, CellData):
            return str(val.value)

        return str(val) if val else ""

    def getSheetIDFromSheetName(self, documentID: str, sheetTitle: str) -> str:
        """
        Returns sheetID from spreadsheet that has title = sheetTitle. If it doesn't exist raises
        IncorrectSheetTitleException
        """

        spreadsheet = self.sheetsService.spreadsheets().get(spreadsheetId=documentID).execute()

        sheetID = None

        for sheet in spreadsheet["sheets"]:
            if sheet["properties"]["title"] == sheetTitle:
                sheetID = sheet["properties"]["sheetId"]

        if not sheetID:
            raise IncorrectSheetTitleException(f"Title {sheetTitle} not found in spreadsheet")

        return sheetID

    def updateEntireRowValuesFromRowNumber(self, rowNumberList: List[int], dataList: List[List[CellData]],
                                           documentID: str,
                                           sheetTitle: str, columnIndex: int = 0):
        """
        Overwrites the entire rowNumber with data
        :param sheetTitle: Sheet title to update
        :param documentID: Document ID of spreadsheet
        :param rowNumberList: 0 indexed row number from google sheets
        :param dataList: New data to be written to rowNumber
        :param columnIndex: Column index to start updating from. Default = 0 meaning update entire row
        :return: None
        """

        sheetID = self.getSheetIDFromSheetName(sheetTitle=sheetTitle, documentID=documentID)

        requests = [{"updateCells": {
            "fields": "*",
            "rows": [{
                "values": [{
                               "userEnteredValue": {
                                   "stringValue": self.getValueAsString(value)
                               }
                           } if value.field_type == FieldType.normal
                           else
                           {
                               "userEnteredValue": {
                                   "stringValue": self.getValueAsString(value)
                               },
                               "dataValidation": {
                                   "condition": {
                                       "type": "ONE_OF_LIST",
                                       "values": [
                                           {"userEnteredValue": val} for val in value.field_values]
                                   },
                                   "strict": True
                               }
                           }
                           for value in dataList[i]]
            }],
            "start": {
                "sheetId": sheetID,
                "rowIndex": rowNumber,
                "columnIndex": columnIndex
            }
        }
        } for i, rowNumber in enumerate(rowNumberList)]
        return self.executeBatchRequest(requests=requests, documentId=documentID)

    def appendValuesToBottomOfSheet(self, data: List[List], documentID, sheetTitle):
        """
        List of Lists with each inner list containing a row of values to be appended
        :param sheetTitle: Title of the sheet within the spreadsheet
        :param documentID: ID of spreadsheet to append to
        :param data: List of rows of values to be appended
        :return:
        """

        sheetID = self.getSheetIDFromSheetName(sheetTitle=sheetTitle, documentID=documentID)

        request = {"appendCells": {
            "fields": "*",
            "rows": [{
                "values": [{
                    "userEnteredValue": {
                        "stringValue": self.getValueAsString(value)
                    }
                } for value in row]
            } for row in data],
            "sheetId": sheetID
        }
        }
        return self.executeBatchRequest(requests=request, documentId=documentID)

    def executeBatchRequest(self, requests, documentId):
        self.sheetsService.spreadsheets().batchUpdate(
            body={'requests': requests, "includeSpreadsheetInResponse": False},
            spreadsheetId=documentId, fields='').execute()
        return True

    def deleteDocument(self, documentId):
        try:
            from apiclient import errors
            response = self.driveService.files().delete(fileId=documentId).execute()
            print(response)
        except errors.HttpError as e:
            print(e)

    def getEntireColumnData(self, sheetID, sheetName, column, column2: str = ""):
        """
        Returns the column data for an entire column
        :param sheetID: Spreadsheet ID
        :param sheetName: Name of the particular sheet within the spreadsheet
        :param column: Column name from A1 notation (see docs: https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/get#:~:text=are%20specified%20using-,A1%20notation,-.%20You%20can%20define)
        :param column2: Second column name for range of columns. Default is empty
        :return: List of strings representing the data in the column
        """
        response = self.sheetsService.spreadsheets().values().get(spreadsheetId=sheetID,
                                                                  range=f"{sheetName}!{column}:{column if not column2 else column2}").execute()
        return [item for item in response["values"]] if "values" in response else []

    def getHeaderFromGoogleSheet(self, sheetID, sheetName):
        response = self.sheetsService.spreadsheets().values().get(spreadsheetId=sheetID,
                                                                  range=f"{sheetName}!1:1").execute()
        return [item for item in response["values"]]

# a = GoogleSheetsService()
# print(a.updateEntireRowValuesFromRowNumber(sheetTitle="tester",
#                                            documentID="19OXMfru14WMEI4nja9SCAljnCDrHlw33SHLO77vAmVo",
#                                            rowNumberList=[316, 317],
#                                            dataList=[['BWA', "HA", "HA", "HA"],
#                                                      ['6', "9", "6", "9"]]))
