import os

from google.oauth2 import service_account
from googleapiclient import discovery

from core.config.googleServiceConfiguration import GOOGLE_DRIVE_SCOPES, GOOGLE_DOCS_SERVICE_NAME, GOOGLE_DRIVE_SERVICE_NAME, \
    GOOGLE_DOCS_API_VERSION, GOOGLE_DRIVE_API_VERSION, GOOGLE_VISION_KEY_PATH as SERVICE_ACCOUNT_CREDENTIALS_PATH, \
    THIRD_PARTY_LEAD_EMAIL_ID, GOOGLE_SHEETS_SERVICE_NAME


class GoogleAppServiceFactory:
    @staticmethod
    def _getServiceAccountCredentials():
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_CREDENTIALS_PATH, scopes=GOOGLE_DRIVE_SCOPES)
        return credentials

    @staticmethod
    def getGoogleAppService(serviceName):
        credentials = GoogleAppServiceFactory._getServiceAccountCredentials()
        if serviceName == GOOGLE_DOCS_SERVICE_NAME:
            return discovery.build(GOOGLE_DOCS_SERVICE_NAME, GOOGLE_DOCS_API_VERSION, credentials=credentials,
                                   cache_discovery=False)
        elif serviceName == GOOGLE_DRIVE_SERVICE_NAME:
            return discovery.build(GOOGLE_DRIVE_SERVICE_NAME, GOOGLE_DRIVE_API_VERSION, credentials=credentials,
                                   cache_discovery=False)
        elif serviceName == GOOGLE_SHEETS_SERVICE_NAME:
            return discovery.build('sheets', 'v4', credentials=credentials,
                                   cache_discovery=False)
        elif serviceName == 'analyticsreporting':
            return discovery.build('analyticsreporting', 'v4', credentials=credentials,
                                   cache_discovery=False)
        elif serviceName == 'gmail':
            return discovery.build('gmail', 'v1', credentials=credentials.with_subject(THIRD_PARTY_LEAD_EMAIL_ID),
                                   cache_discovery=False)
        return None
