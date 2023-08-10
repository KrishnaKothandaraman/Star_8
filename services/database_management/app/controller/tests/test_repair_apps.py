import json
import os
import traceback
import unittest
from unittest.mock import patch

from core.custom_exceptions.general_exceptions import GetStockFromRepairAppsFailedException, \
    StockAllocationFailedException
from core.marketplace_clients.rfclient import RefurbedClient
from core.marketplace_clients.bmclient import BackMarketClient
from services.database_management.app.controller.utils.repair_apps_utils import get_stock_from_repair_apps, Source, \
    perform_stock_check_in_repair_app, StockCheckResult, StockCheckAvailabilityResult, allocate_stock_for_order_items, \
    create_order_in_repair_apps
from dotenv import load_dotenv
load_dotenv()

APP_AUTH_TOKEN = os.environ["REPAIRAPPSACCESSKEY"]


class TestRepairAppsRF(unittest.TestCase):
    @unittest.skip("For now")
    def test_get_stock_from_repair_apps_EU_Purchase(self):
        # assert no exception is raised
        try:
            get_stock_from_repair_apps(Source.EUPurchase)
        except GetStockFromRepairAppsFailedException as e:
            self.fail(e)

    @unittest.skip("For now")
    def test_get_stock_from_repair_apps_Resale(self):
        # assert no exception is raised
        try:
            get_stock_from_repair_apps(Source.Resale)
        except GetStockFromRepairAppsFailedException as e:
            self.fail(e)

    @staticmethod
    def mock_get_stock_from_repair_apps(source: Source):
        if source == Source.EUPurchase:
            return json.loads(
                open("services/database_management/app/controller/tests/test_data/EU_purchase_sample_data.json").read())
        else:
            return json.loads(
                open("services/database_management/app/controller/tests/test_data/resale_list_sample_data.json").read())

    def test_perform_stock_check_in_EU_Purchase(self):

        client = RefurbedClient()
        order = json.loads(open("services/database_management/app/controller/tests/test_data/rf_orders.json").read())[0]
        order_items = client.getOrderItems(order)
        with patch(
                "services.database_management.app.controller.utils.repair_apps_utils.get_stock_from_repair_apps") as mock_get_stock_from_repair_apps:
            mock_get_stock_from_repair_apps.side_effect = self.mock_get_stock_from_repair_apps
            stock_check_result = perform_stock_check_in_repair_app(client, order_items, Source.EUPurchase)
            # assert that the stock check result is correct
            self.assertEqual(stock_check_result.availability_result, StockCheckAvailabilityResult.FULLY_AVAILABLE)
            self.assertEqual(stock_check_result.imei_list, ["351166895223752"])
            self.assertEqual(stock_check_result.sku_list, ["002690SH"])

    def test_perform_stock_check_in_EU_purchase_returns_not_available(self):
        client = RefurbedClient()
        order = json.loads(open("services/database_management/app/controller/tests/test_data/rf_orders.json").read())[
            -1]
        order_items = client.getOrderItems(order)
        with patch(
                "services.database_management.app.controller.utils.repair_apps_utils.get_stock_from_repair_apps") as mock_get_stock_from_repair_apps:
            mock_get_stock_from_repair_apps.side_effect = self.mock_get_stock_from_repair_apps
            stock_check_result = perform_stock_check_in_repair_app(client, order_items, Source.EUPurchase)
            # assert that the stock check result is correct
            self.assertEqual(stock_check_result.availability_result, StockCheckAvailabilityResult.NOT_AVAILABLE)
            self.assertEqual(stock_check_result.imei_list, [])
            self.assertEqual(stock_check_result.sku_list, [])

    def test_perform_stock_check_in_EU_purchase_returns_partially_available(self):
        client = RefurbedClient()
        order_json = json.loads(
            open("services/database_management/app/controller/tests/test_data/rf_orders.json").read())
        # create custom order with one item in stock and one not in stock
        order_json[0]["items"].append(order_json[-1]["items"][0])
        order = order_json[0]
        print(order)
        order_items = client.getOrderItems(order)
        with patch(
                "services.database_management.app.controller.utils.repair_apps_utils.get_stock_from_repair_apps") as mock_get_stock_from_repair_apps:
            mock_get_stock_from_repair_apps.side_effect = self.mock_get_stock_from_repair_apps
            stock_check_result = perform_stock_check_in_repair_app(client, order_items, Source.EUPurchase)
            # assert that the stock check result is correct
            self.assertEqual(stock_check_result.availability_result, StockCheckAvailabilityResult.PARTIALLY_AVAILABLE)
            self.assertEqual(stock_check_result.imei_list, ["351166895223752"])
            self.assertEqual(stock_check_result.sku_list, ["002690SH"])

    def test_perform_stock_check_in_resale(self):

        client = RefurbedClient()
        order = json.loads(open("services/database_management/app/controller/tests/test_data/rf_orders.json").read())[
            -1]
        order_items = client.getOrderItems(order)
        with patch(
                "services.database_management.app.controller.utils.repair_apps_utils.get_stock_from_repair_apps") as mock_get_stock_from_repair_apps:
            mock_get_stock_from_repair_apps.side_effect = self.mock_get_stock_from_repair_apps
            stock_check_result = perform_stock_check_in_repair_app(client, order_items, Source.Resale)
            # assert that the stock check result is correct
            self.assertEqual(stock_check_result.availability_result, StockCheckAvailabilityResult.FULLY_AVAILABLE)
            self.assertEqual(stock_check_result.imei_list, ["353006118658236"])
            self.assertEqual(stock_check_result.sku_list, ["002375BR"])

    def test_perform_stock_check_in_resale_returns_not_available(self):
        client = RefurbedClient()
        order = json.loads(open("services/database_management/app/controller/tests/test_data/rf_orders.json").read())[0]
        order_items = client.getOrderItems(order)
        with patch(
                "services.database_management.app.controller.utils.repair_apps_utils.get_stock_from_repair_apps") as mock_get_stock_from_repair_apps:
            mock_get_stock_from_repair_apps.side_effect = self.mock_get_stock_from_repair_apps
            stock_check_result = perform_stock_check_in_repair_app(client, order_items, Source.Resale)
            # assert that the stock check result is correct
            self.assertEqual(stock_check_result.availability_result, StockCheckAvailabilityResult.NOT_AVAILABLE)
            self.assertEqual(stock_check_result.imei_list, [])
            self.assertEqual(stock_check_result.sku_list, [])

    def test_perform_stock_check_in_resale_returns_partially_available(self):
        client = RefurbedClient()
        order_json = json.loads(
            open("services/database_management/app/controller/tests/test_data/rf_orders.json").read())
        # create custom order with one item in stock and one not in stock
        order_json[-1]["items"].append(order_json[0]["items"][0])
        order = order_json[-1]
        order_items = client.getOrderItems(order)
        with patch(
                "services.database_management.app.controller.utils.repair_apps_utils.get_stock_from_repair_apps") as mock_get_stock_from_repair_apps:
            mock_get_stock_from_repair_apps.side_effect = self.mock_get_stock_from_repair_apps
            stock_check_result = perform_stock_check_in_repair_app(client, order_items, Source.Resale)
            # assert that the stock check result is correct
            self.assertEqual(stock_check_result.availability_result, StockCheckAvailabilityResult.PARTIALLY_AVAILABLE)
            self.assertEqual(stock_check_result.imei_list, ["353006118658236"])
            self.assertEqual(stock_check_result.sku_list, ["002375BR"])

    def test_allocate_stock_for_order_items_fully_available_eu_purchase(self):
        try:
            client = RefurbedClient()
            order = \
                json.loads(open("services/database_management/app/controller/tests/test_data/rf_orders.json").read())[0]
            with patch(
                    "services.database_management.app.controller.utils.repair_apps_utils.get_stock_from_repair_apps") \
                    as mock_get_stock_from_repair_apps, \
                    patch(
                        "services.database_management.app.controller.utils.repair_apps_utils"
                        ".create_order_in_repair_apps") \
                            as mock_create_order_in_repair_apps:
                mock_get_stock_from_repair_apps.side_effect = self.mock_get_stock_from_repair_apps
                mock_create_order_in_repair_apps.return_value = True
                allocate_stock_for_order_items(client, order)
        except StockAllocationFailedException as e:
            self.fail("Stock Allocation Failed")
        except Exception:
            print(traceback.print_exc())
            self.fail("Unexpected Exception")

    def test_allocate_stock_for_order_items_fully_available_resale(self):
        try:
            client = RefurbedClient()
            order = \
                json.loads(open("services/database_management/app/controller/tests/test_data/rf_orders.json").read())[
                    -1]
            with patch(
                    "services.database_management.app.controller.utils.repair_apps_utils.get_stock_from_repair_apps") \
                    as mock_get_stock_from_repair_apps, \
                    patch(
                        "services.database_management.app.controller.utils.repair_apps_utils"
                        ".create_order_in_repair_apps") \
                            as mock_create_order_in_repair_apps:
                mock_get_stock_from_repair_apps.side_effect = self.mock_get_stock_from_repair_apps
                mock_create_order_in_repair_apps.return_value = True
                allocate_stock_for_order_items(client, order)
        except StockAllocationFailedException as e:
            self.fail("Stock Allocation Failed")
        except Exception:
            print(traceback.print_exc())
            self.fail("Unexpected Exception")

    def test_allocate_stock_for_order_items_partially_available_both(self):
        try:
            client = RefurbedClient()
            order_json = \
                json.loads(open("services/database_management/app/controller/tests/test_data/rf_orders.json").read())
            order_json[-1]["items"].append(order_json[0]["items"][0])
            order = order_json[-1]
            with patch(
                    "services.database_management.app.controller.utils.repair_apps_utils.get_stock_from_repair_apps") \
                    as mock_get_stock_from_repair_apps, \
                    patch(
                        "services.database_management.app.controller.utils.repair_apps_utils"
                        ".create_order_in_repair_apps") \
                            as mock_create_order_in_repair_apps:
                mock_get_stock_from_repair_apps.side_effect = self.mock_get_stock_from_repair_apps
                mock_create_order_in_repair_apps.return_value = True
                allocate_stock_for_order_items(client, order)
        except StockAllocationFailedException as e:
            self.fail("Stock Allocation Failed")
        except Exception:
            print(traceback.print_exc())
            self.fail("Unexpected Exception")

    def test_allocate_stock_for_order_items_partially_available_eu_purchase_unavailable_in_resale(self):
        try:
            client = RefurbedClient()
            order_json = \
                json.loads(open("services/database_management/app/controller/tests/test_data/rf_orders.json").read())
            order_json[4]["items"].append(order_json[0]["items"][0])
            order = order_json[4]
            with patch(
                    "services.database_management.app.controller.utils.repair_apps_utils.get_stock_from_repair_apps") \
                    as mock_get_stock_from_repair_apps, \
                    patch(
                        "services.database_management.app.controller.utils.repair_apps_utils"
                        ".create_order_in_repair_apps") \
                            as mock_create_order_in_repair_apps:
                mock_get_stock_from_repair_apps.side_effect = self.mock_get_stock_from_repair_apps
                mock_create_order_in_repair_apps.return_value = True
                self.assertRaises(StockAllocationFailedException,
                                  allocate_stock_for_order_items,
                                  client=client, order=order)
        except Exception:
            print(traceback.print_exc())
            self.fail("Unexpected Exception")


class TestRepairAppsBM(unittest.TestCase):
    @staticmethod
    def mock_get_stock_from_repair_apps(source: Source):
        if source == Source.EUPurchase:
            return json.loads(
                open("services/database_management/app/controller/tests/test_data/EU_purchase_sample_data.json").read())
        else:
            return json.loads(
                open("services/database_management/app/controller/tests/test_data/resale_list_sample_data.json").read())

    def test_perform_stock_check_in_EU_Purchase(self):

        client = BackMarketClient()
        order = json.loads(open("services/database_management/app/controller/tests/test_data/bm_orders.json").read())[0]
        order_items = client.getOrderItems(order)
        with patch(
                "services.database_management.app.controller.utils.repair_apps_utils.get_stock_from_repair_apps") as mock_get_stock_from_repair_apps:
            mock_get_stock_from_repair_apps.side_effect = self.mock_get_stock_from_repair_apps
            stock_check_result = perform_stock_check_in_repair_app(client, order_items, Source.EUPurchase)
            # assert that the stock check result is correct
            self.assertEqual(stock_check_result.availability_result, StockCheckAvailabilityResult.FULLY_AVAILABLE)
            self.assertEqual(stock_check_result.imei_list, ["356714114422526"])
            self.assertEqual(stock_check_result.sku_list, ["002713SL"])

    def test_perform_stock_check_in_EU_purchase_returns_not_available(self):
        client = BackMarketClient()
        order = json.loads(open("services/database_management/app/controller/tests/test_data/bm_orders.json").read())[
            -1]
        order_items = client.getOrderItems(order)
        with patch(
                "services.database_management.app.controller.utils.repair_apps_utils.get_stock_from_repair_apps") as mock_get_stock_from_repair_apps:
            mock_get_stock_from_repair_apps.side_effect = self.mock_get_stock_from_repair_apps
            stock_check_result = perform_stock_check_in_repair_app(client, order_items, Source.EUPurchase)
            # assert that the stock check result is correct
            self.assertEqual(stock_check_result.availability_result, StockCheckAvailabilityResult.NOT_AVAILABLE)
            self.assertEqual(stock_check_result.imei_list, [])
            self.assertEqual(stock_check_result.sku_list, [])

    def test_perform_stock_check_in_EU_purchase_returns_partially_available(self):
        client = BackMarketClient()
        order_json = json.loads(
            open("services/database_management/app/controller/tests/test_data/bm_orders.json").read())
        # create custom order with one item in stock and one not in stock
        order_json[0]["orderlines"].append(order_json[1]["orderlines"][0])
        order = order_json[0]
        print(order)
        order_items = client.getOrderItems(order)
        with patch(
                "services.database_management.app.controller.utils.repair_apps_utils.get_stock_from_repair_apps") as mock_get_stock_from_repair_apps:
            mock_get_stock_from_repair_apps.side_effect = self.mock_get_stock_from_repair_apps
            stock_check_result = perform_stock_check_in_repair_app(client, order_items, Source.EUPurchase)
            # assert that the stock check result is correct
            self.assertEqual(stock_check_result.availability_result, StockCheckAvailabilityResult.PARTIALLY_AVAILABLE)
            self.assertEqual(stock_check_result.imei_list, ["356714114422526"])
            self.assertEqual(stock_check_result.sku_list, ["002713SL"])

    def test_perform_stock_check_in_resale(self):

        client = BackMarketClient()
        order = json.loads(open("services/database_management/app/controller/tests/test_data/bm_orders.json").read())[
            1]
        order_items = client.getOrderItems(order)
        with patch(
                "services.database_management.app.controller.utils.repair_apps_utils.get_stock_from_repair_apps") as mock_get_stock_from_repair_apps:
            mock_get_stock_from_repair_apps.side_effect = self.mock_get_stock_from_repair_apps
            stock_check_result = perform_stock_check_in_repair_app(client, order_items, Source.Resale)
            # assert that the stock check result is correct
            self.assertEqual(stock_check_result.availability_result, StockCheckAvailabilityResult.FULLY_AVAILABLE)
            self.assertEqual(stock_check_result.imei_list, ["356696111956855"])
            self.assertEqual(stock_check_result.sku_list, ["002592SH"])

    def test_perform_stock_check_in_resale_returns_not_available(self):
        client = BackMarketClient()
        order = json.loads(open("services/database_management/app/controller/tests/test_data/bm_orders.json").read())[0]
        order_items = client.getOrderItems(order)
        with patch(
                "services.database_management.app.controller.utils.repair_apps_utils.get_stock_from_repair_apps") as mock_get_stock_from_repair_apps:
            mock_get_stock_from_repair_apps.side_effect = self.mock_get_stock_from_repair_apps
            stock_check_result = perform_stock_check_in_repair_app(client, order_items, Source.Resale)
            # assert that the stock check result is correct
            self.assertEqual(stock_check_result.availability_result, StockCheckAvailabilityResult.NOT_AVAILABLE)
            self.assertEqual(stock_check_result.imei_list, [])
            self.assertEqual(stock_check_result.sku_list, [])

    def test_perform_stock_check_in_resale_returns_partially_available(self):
        client = BackMarketClient()
        order_json = json.loads(
            open("services/database_management/app/controller/tests/test_data/bm_orders.json").read())
        # create custom order with one item in stock and one not in stock
        order_json[1]["orderlines"].append(order_json[0]["orderlines"][0])
        order = order_json[1]
        order_items = client.getOrderItems(order)
        with patch(
                "services.database_management.app.controller.utils.repair_apps_utils.get_stock_from_repair_apps") as mock_get_stock_from_repair_apps:
            mock_get_stock_from_repair_apps.side_effect = self.mock_get_stock_from_repair_apps
            stock_check_result = perform_stock_check_in_repair_app(client, order_items, Source.Resale)
            # assert that the stock check result is correct
            self.assertEqual(stock_check_result.availability_result, StockCheckAvailabilityResult.PARTIALLY_AVAILABLE)
            self.assertEqual(stock_check_result.imei_list, ["356696111956855"])
            self.assertEqual(stock_check_result.sku_list, ["002592SH"])

    def test_allocate_stock_for_order_items_fully_available_eu_purchase(self):
        try:
            client = BackMarketClient()
            order = \
                json.loads(open("services/database_management/app/controller/tests/test_data/bm_orders.json").read())[0]
            with patch(
                    "services.database_management.app.controller.utils.repair_apps_utils.get_stock_from_repair_apps") \
                    as mock_get_stock_from_repair_apps, \
                    patch(
                        "services.database_management.app.controller.utils.repair_apps_utils"
                        ".create_order_in_repair_apps") \
                            as mock_create_order_in_repair_apps:
                mock_get_stock_from_repair_apps.side_effect = self.mock_get_stock_from_repair_apps
                mock_create_order_in_repair_apps.return_value = True
                allocate_stock_for_order_items(client, order)
        except StockAllocationFailedException as e:
            self.fail("Stock Allocation Failed")
        except Exception:
            print(traceback.print_exc())
            self.fail("Unexpected Exception")

    def test_allocate_stock_for_order_items_fully_available_resale(self):
        try:
            client = BackMarketClient()
            order = \
                json.loads(open("services/database_management/app/controller/tests/test_data/bm_orders.json").read())[1]
            with patch(
                    "services.database_management.app.controller.utils.repair_apps_utils.get_stock_from_repair_apps") \
                    as mock_get_stock_from_repair_apps, \
                    patch(
                        "services.database_management.app.controller.utils.repair_apps_utils"
                        ".create_order_in_repair_apps") \
                            as mock_create_order_in_repair_apps:
                mock_get_stock_from_repair_apps.side_effect = self.mock_get_stock_from_repair_apps
                mock_create_order_in_repair_apps.return_value = True
                allocate_stock_for_order_items(client, order)
        except StockAllocationFailedException as e:
            self.fail("Stock Allocation Failed")
        except Exception:
            print(traceback.print_exc())
            self.fail("Unexpected Exception")

    def test_allocate_stock_for_order_items_partially_available_both(self):
        try:
            client = BackMarketClient()
            order_json = \
                json.loads(open("services/database_management/app/controller/tests/test_data/bm_orders.json").read())
            order_json[1]["orderlines"].append(order_json[0]["orderlines"][0])
            order = order_json[1]
            with patch(
                    "services.database_management.app.controller.utils.repair_apps_utils.get_stock_from_repair_apps") \
                    as mock_get_stock_from_repair_apps, \
                    patch(
                        "services.database_management.app.controller.utils.repair_apps_utils"
                        ".create_order_in_repair_apps") \
                            as mock_create_order_in_repair_apps:
                mock_get_stock_from_repair_apps.side_effect = self.mock_get_stock_from_repair_apps
                mock_create_order_in_repair_apps.return_value = True
                allocate_stock_for_order_items(client, order)
        except StockAllocationFailedException as e:
            self.fail("Stock Allocation Failed")
        except Exception:
            print(traceback.print_exc())
            self.fail("Unexpected Exception")

    def test_allocate_stock_for_order_items_partially_available_eu_purchase_unavailable_in_resale(self):
        try:
            client = BackMarketClient()
            order_json = \
                json.loads(open("services/database_management/app/controller/tests/test_data/bm_orders.json").read())
            order_json[4]["orderlines"].append(order_json[0]["orderlines"][0])
            order = order_json[4]
            with patch(
                    "services.database_management.app.controller.utils.repair_apps_utils.get_stock_from_repair_apps") \
                    as mock_get_stock_from_repair_apps, \
                    patch(
                        "services.database_management.app.controller.utils.repair_apps_utils"
                        ".create_order_in_repair_apps") \
                            as mock_create_order_in_repair_apps:
                mock_get_stock_from_repair_apps.side_effect = self.mock_get_stock_from_repair_apps
                mock_create_order_in_repair_apps.return_value = True
                self.assertRaises(StockAllocationFailedException,
                                  allocate_stock_for_order_items,
                                  client=client, order=order)
        except Exception:
            print(traceback.print_exc())
            self.fail("Unexpected Exception")


class TestAppSheetAddOrder(unittest.TestCase):
    @patch('services.database_management.app.controller.utils.repair_apps_utils.requests.post')
    def test_create_order_in_repair_apps(self, mock_post):
        # Define mock response
        mock_response = unittest.mock.Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Define mock stock result
        mock_stock_result = StockCheckResult(imei_list=['351166895223752'],
                                             sku_list=['002690SH'],
                                             availability_result=StockCheckAvailabilityResult.FULLY_AVAILABLE)
        order_json = \
            json.loads(open("services/database_management/app/controller/tests/test_data/rf_orders.json").read())[0]

        mock_formatted_order = RefurbedClient().convertOrderToSheetColumns(order_json)[0]
        mock_source = Source.EUPurchase
        # Call the function
        create_order_in_repair_apps(mock_formatted_order, mock_stock_result, mock_source)

        # Assert the mock request is called with the correct data
        expected_payload = {
                "Action": "add",
                "Properties": {
                    "Locale": "en-US",
                    "Location": "47.623098, -122.330184",
                    "Timezone": "Pacific Standard Time",
                    "UserSettings": {
                        "Option 1": "value1",
                        "Option 2": "value2"
                    }
                },
                "Rows": [
                    {
                        "IMEI": "351166895223752",
                        "order_id": "6335576",
                        "first_name": "Arthur",
                        "last_name": "Kluin",
                        "street": "Laan van avant-garde",
                        "street2": "458",
                        "postal_code": "3059 VA",
                        "country": "NL",
                        "city": "Rotterdam",
                        "phone": "+31620362424",
                        "email": "arthur_kluin@hotmail.com"
                    }
                ]
            }

        mock_post.assert_called_once_with(url=mock_source.get_add_order_url_from_source(mock_source),
                                          headers={'applicationAccessKey': APP_AUTH_TOKEN},
                                          json=expected_payload)
