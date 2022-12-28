import io
from typing import List, Dict
from gdoctableapppy import gdoctableapp
from googleapiclient.http import MediaIoBaseDownload

from core.config.googleServiceConfiguration import GOOGLE_DRIVE_SERVICE_NAME, GOOGLE_SHEETS_SERVICE_NAME
from core.google_services.googleAppServiceFactory import GoogleAppServiceFactory

GOOGLE_SHEETS_STARTING_CELL = "A15"


class GoogleSheetsService:
    def __init__(self):
        self.driveService = GoogleAppServiceFactory.getGoogleAppService(GOOGLE_DRIVE_SERVICE_NAME)
        self.sheetsService = GoogleAppServiceFactory.getGoogleAppService(GOOGLE_SHEETS_SERVICE_NAME)

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
