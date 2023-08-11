import json
import os
import unittest
from typing import List, Dict
from unittest.mock import patch, MagicMock

import pytest
import difflib
from core.google_services.googleSheetsService import GoogleSheetsService
from core.marketplace_clients.bmclient import BackMarketClient
from core.marketplace_clients.rfclient import RefurbedClient
from services.database_management.app.app import app
from services.database_management.app.controller.orders_database import batchUpdateGoogleSheetWithOrderIDs, \
    get_bm_orders_from_marketplace, get_rf_orders_from_marketplace, get_update_data_from_orders, \
    update_sheet_with_new_orders
import services.database_management.app.controller.tests.test_data.sample_formatted_data as sample_data

APP_AUTH_TOKEN = os.environ["APPAUTHTOKEN"]
BM_ORDERS_JSON_FILEPATH = 'services/database_management/app/controller/tests/test_data/bm_orders.json'
RF_ORDERS_JSON_FILEPATH = 'services/database_management/app/controller/tests/test_data/rf_orders.json'
SHEETS_SERVICE_FILE_PATH = "core/google_services/googleSheetsService/GoogleSheetsService"
ORDERS_DB_FILEPATH = "services/database_management/app/controller/orders_database"


def test_batchUpdateGoogleSheetWithOrderIDs_success(mock_bm_orders, mock_rf_orders):
    with patch.object(RefurbedClient, 'getOrderByID') as rf_mock_get_order_by_id, \
            patch.object(BackMarketClient, 'getOrderByID') as bm_mock_get_order_by_id, \
            patch.object(GoogleSheetsService, 'getEntireColumnData') as mock_get_col_data, \
            patch.object(GoogleSheetsService, 'updateEntireRowValuesFromRowNumber') as mock_update_row_values:
        rf_mock_get_order_by_id.side_effect = lambda orderID: next(
            order for order in mock_rf_orders if str(order['id']) == orderID)

        rf_mock_get_order_by_id.side_effect = lambda orderID: next(
            order for order in mock_rf_orders if str(order['id']) == orderID)

        bm_mock_get_order_by_id.side_effect = lambda orderID: next(
            order for order in mock_bm_orders if str(order['order_id']) == orderID)

        bm_mock_get_order_by_id.side_effect = lambda orderID: next(
            order for order in mock_bm_orders if str(order['order_id']) == orderID)

        googleSheetOrderIDs = [['29032497'], ['29023751'], ['28882249'], ['29012076'], ['28833152'], ['6335576'],
                               ['6335559'], ['6278377'], ['6278348'], ['6278249'], ['6278117']]
        googleSheetItemIDs = [['29176811'], ['29167979'], ['29025446'], ['29161275'], ['28979372'], ['7514453'],
                              ['7514431'], ['7514431'], ['7514431'], ['7514431'], ['7514431']]

        mock_get_col_data.getEntireColumnData.side_effect = \
            lambda sheetID, sheetName, column: googleSheetOrderIDs if column == "A" else googleSheetItemIDs
        mock_update_row_values.return_value.updateEntireRowValuesFromRowNumber = MagicMock()

        # Create a test client using the Flask app
        client = app.test_client()

        # Make a request to the route with valid data
        headers = {'auth-token': APP_AUTH_TOKEN}
        data = {'rf_orders': ["6335576",
                              "6335559",
                              "6278377",
                              "6278348",
                              "6278249",
                              "6278117"],
                'bm_orders': ["29032497",
                              "29023751",
                              "28882249",
                              "29017076",
                              "28833152"]}
        response = client.post('/batch-update-googlesheet', headers=headers, json=data)

        # Assert the response status code and content
        assert response.status_code == 200
        assert response.json == {'type': 'success', 'message': 'Updated RF: 6, BM: 5'}


def test_batchUpdateGoogleSheetWithOrderIDs_invalid_auth_token():
    # Create a test client using the Flask app
    client = app.test_client()

    # Make a request to the route with an invalid auth token
    headers = {'auth-token': 'invalid_token'}
    data = {'rf_orders': ['123', '456', '789'],
            'bm_orders': ['123', '456', '789']}
    response = client.post('/batch-update-googlesheet', headers=headers, json=data)

    # Assert the response status code and content
    assert response.status_code == 401
    assert response.json == {'type': 'fail', 'message': 'Incorrect auth token provided'}


@unittest.skip("Removed 10 order limit")
def test_batchUpdateGoogleSheetWithOrderIDs_with_more_than_10_orders_returning_error():
    # Create a test client using the Flask app
    client = app.test_client()

    # Make a request to the route with an invalid auth token
    headers = {'auth-token': APP_AUTH_TOKEN}
    data = {'rf_orders': ['123', '456', '789', '123', '456', '789', '123', '456', '789', '123', '456', '789'],
            'bm_orders': ['123', '456', '789', '123', '456', '789', '123', '456', '789', '123', '456', '789']}
    response = client.post('/batch-update-googlesheet', headers=headers, json=data)

    # Assert the response status code and content
    assert response.status_code == 400
    assert response.json == {'type': 'fail', 'message': 'Keep orders under 10 per marketplace in each request!'}


def test_batchUpdateGoogleSheetWithOrderIDs_invalid_body():
    # Create a test client using the Flask app
    client = app.test_client()

    # Make a request to the route with invalid data to trigger an exception
    headers = {'auth-token': APP_AUTH_TOKEN}
    data = {'invalid_key': 'invalid_value'}
    response = client.post('/batch-update-googlesheet', headers=headers, json=data)

    # Assert the response status code and content
    assert response.status_code == 400
    assert response.json == {'type': 'fail', 'message': "Key `rf_orders` or `bm_orders` not in body"}


@unittest.skip("Skipping test_batchUpdateGoogleSheetWithOrderIDs")
def test_batchUpdateGoogleSheetWithOrderIDs():
    with patch.object(BackMarketClient, 'getOrderByID') as mock_get_order_by_id:
        with open('services/database_management/app/controller/tests/test_data/bm_orders.json') as json_file:
            bm_orders = json.load(json_file)

        mock_get_order_by_id.side_effect = lambda orderID: next(
            order for order in bm_orders if str(order['order_id']) == orderID)

        # Invoke the function with the mocked API calls
        client = app.test_client()

        headers = {'auth-token': APP_AUTH_TOKEN}
        data = {'rf_orders': ["29032497",
                              "29023751",
                              "28882249",
                              "29017076",
                              "28833152"],
                'bm_orders': ["6335576",
                              "6335559",
                              "6278377",
                              "6278348",
                              "6278249",
                              "6278117"]}
        response = client.post('/batch-update-googlesheet', headers=headers, json=data)

        assert response.status_code == 200
        assert response.json == {
            "type": "success",
            "message": "Updated RF: 5, BM: 6"
        }


@pytest.fixture
def mock_bm_orders():
    with open(BM_ORDERS_JSON_FILEPATH) as json_file:
        bm_orders = json.load(json_file)
    return bm_orders


@pytest.fixture
def mock_rf_orders():
    with open(RF_ORDERS_JSON_FILEPATH) as json_file:
        rf_orders = json.load(json_file)
    return rf_orders


def test_get_bm_orders_from_marketplace(mock_bm_orders):
    with patch.object(BackMarketClient, 'getOrderByID') as mock_get_order_by_id:
        mock_get_order_by_id.side_effect = lambda orderID: next(
            order for order in mock_bm_orders if str(order['order_id']) == orderID)

        mock_get_order_by_id.side_effect = lambda orderID: next(
            order for order in mock_bm_orders if str(order['order_id']) == orderID)
        BMInstance = BackMarketClient()
        orderIDs = ["29032497",
                    "29023751",
                    "28882249",
                    "29017076",
                    "28833152"]

        result = get_bm_orders_from_marketplace(BMInstance, orderIDs)

        assert result == [mock_bm_orders[0], mock_bm_orders[1], mock_bm_orders[2], mock_bm_orders[3], mock_bm_orders[4]]


def test_get_rf_orders_from_marketplace(mock_rf_orders):
    with patch.object(RefurbedClient, 'getOrderByID') as mock_get_order_by_id:
        mock_get_order_by_id.side_effect = lambda orderID: next(
            order for order in mock_rf_orders if str(order['id']) == orderID)

        mock_get_order_by_id.side_effect = lambda orderID: next(
            order for order in mock_rf_orders if str(order['id']) == orderID)

        RFInstance = RefurbedClient()
        orderIDs = ["6335576",
                    "6335559",
                    "6278377",
                    "6278348",
                    "6278249",
                    "6278117"]
        result = get_rf_orders_from_marketplace(RFInstance, orderIDs)

        assert result == [mock_rf_orders[0], mock_rf_orders[1], mock_rf_orders[2], mock_rf_orders[3], mock_rf_orders[4],
                          mock_rf_orders[5]]


def get_rf_test_orders() -> List[Dict]:
    with open(RF_ORDERS_JSON_FILEPATH) as json_file:
        rf_orders = json.load(json_file)
    return rf_orders


def get_bm_test_orders() -> List[Dict]:
    with open(BM_ORDERS_JSON_FILEPATH) as json_file:
        bm_orders = json.load(json_file)
    return bm_orders


@pytest.mark.parametrize("new_orders, api_instance, googleSheetIDS, expected_result", [
    # Test case 1
    (
            get_rf_test_orders(),
            RefurbedClient(),
            {"6335576_7514453": 1, "6335559_7514431": 2, "6278377_7514431": 3, "6278348_7514431": 4,
             "6278249_7514431": 5, "6278117_7514431": 6},
            sample_data.RF_FORMATTED_DATA
    ),
    # Add more test cases as needed
])
@unittest.skip("sfds")
def test_get_rf_update_data_from_orders(new_orders, api_instance, googleSheetIDS, expected_result):
    result = get_update_data_from_orders(new_orders, api_instance, googleSheetIDS)
    assert result == expected_result


@pytest.mark.parametrize("new_orders, api_instance, googleSheetIDS, expected_result", [
    # Test case 1
    (
            get_bm_test_orders(),
            BackMarketClient(),
            {"29032497_29176811": 1, "29023751_29167979": 2, "28882249_29025446": 3,
             "29012076_29161275": 4, "28833152_28979372": 5},
            sample_data.BM_FORMATTED_DATA
    ),
    # Add more test cases as needed
])
def test_get_bm_update_data_from_orders(new_orders, api_instance, googleSheetIDS, expected_result):
    result = get_update_data_from_orders(new_orders, api_instance, googleSheetIDS)
    assert len(result) == len(expected_result)


def test_update_sheet_with_new_orders():
    rf_orders = get_rf_test_orders()
    bm_orders = get_bm_test_orders()
    RFAPIInstance = RefurbedClient()
    BMAPIInstance = BackMarketClient()

    with patch.object(GoogleSheetsService, 'getEntireColumnData') as mock_get_col_data, \
            patch.object(GoogleSheetsService, 'updateEntireRowValuesFromRowNumber') as mock_update_row_values:
        googleSheetOrderIDs = [['29032497'], ['29023751'], ['28882249'], ['29012076'], ['28833152'], ['6335576'],
                               ['6335559'], ['6278377'], ['6278348'], ['6278249'], ['6278117']]
        googleSheetItemIDs = [['29176811'], ['29167979'], ['29025446'], ['29161275'], ['28979372'], ['7514453'],
                              ['7514431'], ['7514431'], ['7514431'], ['7514431'], ['7514431']]
        mock_get_col_data.getEntireColumnData.side_effect = \
            lambda sheetID, sheetName, column: googleSheetOrderIDs if column == "A" else googleSheetItemIDs
        mock_update_row_values.return_value.updateEntireRowValuesFromRowNumber = MagicMock()
        result = update_sheet_with_new_orders(rf_orders, bm_orders, RFAPIInstance, BMAPIInstance,
                                              mock_get_col_data)
        expected_result = sample_data.CELL_FORMATTED_DATA
        # for i, s in enumerate(difflib.ndiff(str(result), expected_result)):
        #     if s[0] == ' ':
        #         continue
        #     elif s[0] == '-':
        #         print(u'Delete "{}" from position {}'.format(s[-1], i))
        #     elif s[0] == '+':
        #         print(u'Add "{}" to position {}'.format(s[-1], i))
        # print()
        assert str(result) == expected_result
