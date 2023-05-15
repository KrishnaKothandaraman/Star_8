import os
import unittest
from unittest import mock
from unittest.mock import patch
from unittest.mock import MagicMock
from services.database_management.app.app import app
from services.database_management.app.controller.orders_database import updateGoogleSheet, \
    performUpdateExistingOrdersUpdate, SPREADSHEET_ID, SPREADSHEET_NAME

APP_AUTH_TOKEN = os.environ["APPAUTHTOKEN"]


class TestUpdateExistingOrdersUpdate(unittest.TestCase):
    def test_performUpdateExistingOrdersUpdate_with_no_new_orders(self):
        # Create mock objects for dependencies
        service_mock = MagicMock()
        BMAPIInstance_mock = MagicMock()
        RFAPIInstance_mock = MagicMock()

        # Set up the mock return values for the mocked functions
        service_mock.getEntireColumnData.return_value = [["Order1", "Order2"], ["Item1", "Item2"]]
        RFAPIInstance_mock.getOrdersBetweenDates.return_value = [
            {"id": "Order1", "items": [{"id": "Item1"}]},
            {"id": "Order3", "items": [{"id": "Item4"}]}
        ]
        BMAPIInstance_mock.getOrdersBetweenDates.return_value = [
            {"order_id": "Order2", "orderlines": [{"id": "Item2"}]},
            {"order_id": "Order4", "orderlines": [{"id": "Item5"}]}
        ]
        BMAPIInstance_mock.itemKeyName = "orderlines"
        BMAPIInstance_mock.orderIDFieldName = "order_id"
        RFAPIInstance_mock.itemKeyName = "items"
        RFAPIInstance_mock.orderIDFieldName = "id"

        # Call the function under test
        result = performUpdateExistingOrdersUpdate(service_mock, BMAPIInstance_mock, RFAPIInstance_mock)

        service_mock.getEntireColumnData.assert_has_calls([
            mock.call(sheetID=SPREADSHEET_ID, sheetName=SPREADSHEET_NAME, column="A"),
            mock.call(sheetID=SPREADSHEET_ID, sheetName=SPREADSHEET_NAME, column="AQ"),
        ])

        self.assertEqual(result, [])  # Assert the number of orders updated

    @unittest.skip("TODO: Fix this test")
    def test_performUpdateExistingOrdersUpdate_with_new_orders(self):
        # Create mock objects for dependencies
        service_mock = MagicMock()
        BMAPIInstance_mock = MagicMock()
        RFAPIInstance_mock = MagicMock()

        # Set up the mock return values for the mocked functions
        # Mock the return data for getEntireColumnData method
        def side_effect(sheetID, sheetName, column):
            if column == "A":
                return [["Order_ids"], ["Order1"], ["Order2"], ["Order3"], ["Order4"]]
            elif column == "AQ":
                return [["Item_ids"], ["Item1"], ["Item2"], ["Item3"], ["Item4"]]
            else:
                return None

        service_mock.getEntireColumnData.side_effect = side_effect
        RFAPIInstance_mock.getOrdersBetweenDates.return_value = [
            {"id": "Order1", "items": [{"id": "Item1"}]},
            {"id": "Order3", "items": [{"id": "Item4"}]}
        ]
        BMAPIInstance_mock.getOrdersBetweenDates.return_value = [
            {"order_id": "Order2", "orderlines": [{"id": "Item2"}]},
            {"order_id": "Order4", "orderlines": [{"id": "Item5"}]}
        ]

        # Call the function under test
        result = performUpdateExistingOrdersUpdate(service_mock, BMAPIInstance_mock, RFAPIInstance_mock)

        service_mock.getEntireColumnData.assert_has_calls([
            mock.call(sheetID=SPREADSHEET_ID, sheetName=SPREADSHEET_NAME, column="A"),
            mock.call(sheetID=SPREADSHEET_ID, sheetName=SPREADSHEET_NAME, column="AQ"),
        ])

        service_mock.updateEntireRowValuesFromRowNumber.assert_called_with(
            sheetTitle=SPREADSHEET_NAME,
            documentID=SPREADSHEET_ID,
            dataList=[['Order1', 'Item1'], ['Order2', 'Item2']],
            rowNumberList=[1, 2]
        )
        self.assertEqual(result, 2)  # Assert the number of orders updated

    def test_updateGoogleSheet_with_days(self):
        # Mock the API calls
        with patch(
                "services.database_management.app.controller.orders_database.performUpdateExistingOrdersUpdate") as mock_update_orders_update, \
                patch(
                    "services.database_management.app.controller.orders_database.performAddNewOrdersUpdate") as mock_add_orders_update:
            # Configure the return values of the mocked functions
            mock_update_orders_update.return_value = ["*"] * 5
            mock_add_orders_update.return_value = 10

            client = app.test_client()
            # Make a request to the route with an invalid auth token
            headers = {'auth-token': APP_AUTH_TOKEN}
            data = {'days': 7}
            response = client.post('/update-googlesheet', headers=headers, json=data)

            # Assert the expected behavior and outcomes
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, {
                "type": "success",
                "message": "Added 10 records! Updated 5 records!"
            })

    def test_updateGoogleSheet__invalid_auth_token(self):
        # Create a test client using the Flask app
        with patch("core.google_services.googleSheetsService.GoogleSheetsService"), \
                patch("core.marketplace_clients.rfclient.RefurbedClient"), \
                patch("core.marketplace_clients.bmclient.BackMarketClient"):
            client = app.test_client()

            # Make a request to the route with an invalid auth token
            headers = {'auth-token': 'invalid_token'}
            data = {'days': 7}
            response = client.post('/update-googlesheet', headers=headers, json=data)

            # Assert the response status code and content
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.json,
                             {'type': 'fail', 'message': 'Incorrect auth token provided'})

#
#
# def test_updateGoogleSheet_with_single_order_id(mock_request):
#     # Mock the API calls
#     with patch("my_module.GoogleSheetsService") as mock_gsheets, \
#             patch("my_module.RefurbedClient") as mock_rf_client, \
#             patch("my_module.BackMarketClient") as mock_bm_client, \
#             patch("my_module.performAddNewOrdersUpdate") as mock_add_orders_update:
#         # Configure the return values of the mocked functions
#         mock_gsheets_instance = mock_gsheets.return_value
#         mock_rf_instance = mock_rf_client.return_value
#         mock_bm_instance = mock_bm_client.return_value
#         mock_add_orders_update.return_value = 10
#
#         # Set up the mock request and JSON payload
#         mock_request.headers.get.return_value = "auth-token"
#         mock_request.get_json.return_value = {
#             "single_order_id": "order123",
#             "vendor": "refurbed"
#         }
#
#         # Invoke the function with the mocked dependencies
#         response = updateGoogleSheet()
#
#         # Assert the expected behavior and outcomes
#         assert response.status_code == 200
#         assert response.json == {
#             "type": "success",
#             "message": "Added 10 records! Updated 1 records!"
#         }
#
#         # Additional assertions for the mocked dependencies
#         mock_gsheets.assert_called_once()
#         mock_rf_client.assert_called_once()
#         mock_bm_client.assert_called_once()
#         mock_add_orders_update.assert_called_once_with(
#             service=mock_gsheets_instance,
#             BMAPIInstance=mock_bm_instance,
#             RFAPIInstance=mock_rf_instance,
#             days=0,
#             single_order_id="order123",
#             single_order_id_vendor="refurbed"
#         )
#
#
