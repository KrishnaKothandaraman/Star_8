import sys
import os

# add root to paths
sys.path.append(os.path.join(""))

from core.custom_exceptions.general_exceptions import IncorrectSheetTitleException
import io
from typing import List, Dict, Tuple
import apiclient
import googleapiclient.http
from gdoctableapppy import gdoctableapp
from googleapiclient.http import MediaIoBaseDownload
from core.config.googleServiceConfiguration import GOOGLE_DRIVE_SERVICE_NAME, GOOGLE_SHEETS_SERVICE_NAME
from core.google_services.googleAppServiceFactory import GoogleAppServiceFactory

GOOGLE_SHEETS_STARTING_CELL = "A15"

"""
Docs: https://googleapis.github.io/google-api-python-client/docs/dyn/sheets_v4.spreadsheets.html#getByDataFilter
"""


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

        return str(val) if val else ""

    def appendValuesToBottomOfSheet(self, data: List[List], documentID, sheetTitle):
        """
        List of Lists with each inner list containing a row of values to be appended
        :param sheetTitle: Title of the sheet within the spreadsheet
        :param documentID: ID of spreadsheet to append to
        :param data: List of rows of values to be appended
        :return:
        """
        spreadsheet = self.sheetsService.spreadsheets().get(spreadsheetId=documentID).execute()

        sheetID = None

        for sheet in spreadsheet["sheets"]:
            if sheet["properties"]["title"] == sheetTitle:
                sheetID = sheet["properties"]["sheetId"]

        if not sheetID:
            raise IncorrectSheetTitleException(f"Title {sheetTitle} not found in spreadsheet")

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

    def getEntireColumnData(self, sheetID, sheetName, column):
        """
        Returns the column data for an entire column
        :param sheetID: Spreadsheet ID
        :param sheetName: Name of the particular sheet within the spreadsheet
        :param column: Column name from A1 notation (see docs: https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/get#:~:text=are%20specified%20using-,A1%20notation,-.%20You%20can%20define)
        :return: List of strings representing the data in the column
        """
        response = self.sheetsService.spreadsheets().values().get(spreadsheetId=sheetID,
                                                                  range=f"{sheetName}!{column}:{column}").execute()
        return [item for item in response["values"]] if "values" in response else []

    def getHeaderFromGoogleSheet(self, sheetID, sheetName):
        response = self.sheetsService.spreadsheets().values().get(spreadsheetId=sheetID,
                                                                  range=f"{sheetName}!1:1").execute()
        return [item for item in response["values"]]

# a = GoogleSheetsService() a.appendValuesToBottomOfSheet(sheetTitle="MyRand",
# documentID="1BhDJ-RJwbq6wQtAsoZoN5YY5InK5Z2Qc15rHgLzo4Ys", data=[[1, 2, 3], [4, 5, {"a"}]])

