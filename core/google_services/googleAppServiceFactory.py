import os
from google.oauth2 import service_account
from googleapiclient import discovery
from core.custom_exceptions.google_service_exceptions import InvalidGoogleServiceException
from core.config.googleServiceConfiguration import GOOGLE_SHEETS_SCOPES, GOOGLE_DRIVE_SCOPES, GOOGLE_DOCS_SERVICE_NAME, GOOGLE_DRIVE_SERVICE_NAME, \
    GOOGLE_DOCS_API_VERSION, GOOGLE_DRIVE_API_VERSION, GOOGLE_VISION_KEY_PATH as SERVICE_ACCOUNT_CREDENTIALS_PATH, \
    THIRD_PARTY_LEAD_EMAIL_ID, GOOGLE_SHEETS_SERVICE_NAME


class GoogleAppServiceFactory:
    @staticmethod
    def _getServiceAccountCredentials(scopes):
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_CREDENTIALS_PATH, scopes=scopes)
        return credentials

    @staticmethod
    def getGoogleAppService(serviceName):
        if serviceName == GOOGLE_SHEETS_SERVICE_NAME:
            credentials = GoogleAppServiceFactory._getServiceAccountCredentials(GOOGLE_SHEETS_SCOPES)
            return discovery.build('sheets', 'v4', credentials=credentials,
                                   cache_discovery=False)
        elif serviceName == GOOGLE_DRIVE_SERVICE_NAME:
            credentials = GoogleAppServiceFactory._getServiceAccountCredentials(GOOGLE_DRIVE_SCOPES)
            return discovery.build(GOOGLE_DRIVE_SERVICE_NAME, GOOGLE_DRIVE_API_VERSION, credentials=credentials,
                                   cache_discovery=False)
        else:
            raise InvalidGoogleServiceException(message=f"{serviceName} not implemented")
