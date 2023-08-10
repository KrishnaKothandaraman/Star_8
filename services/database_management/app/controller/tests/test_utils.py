import os
import unittest
from services.database_management.app.controller.utils.swd_utils import getStockFromItems

APP_AUTH_TOKEN = os.environ["APPAUTHTOKEN"]


class TestSWDUtils(unittest.TestCase):
    def test_stock_check_calculation_returns_zero_with_non_zero_master_atp(self):
        test_resp = {'144290': {'sku': 144290, 'barcode': '002516SH', 'reference': '002516SH', 'reference2': '002516SH',
                                'description': 'iPhone SE 3 128GB Midnight EUS (Shiny)', 'warehouse_id': 1,
                                'weight': 630, 'dimensions': {'length': 210, 'width': 144, 'height': 70},
                                'items_in_box': 1, 'level': 0, 'atp': 0, 'master_level': 0, 'master_atp': 10,
                                'status': 1, 'status_string': 'on', 'lot_number': '', 'tht_alert': 'none',
                                'tht_date': False, 'tht_minimum': False,
                                'last_update': {'date': '2023-05-23 07:18:23', 'timezone_type': 3,
                                                'timezone': 'Europe/Brussels'},
                                'last_atp_update': {'date': '2023-05-23 07:18:23', 'timezone_type': 3,
                                                    'timezone': 'Europe/Brussels'}},
                     '184242': {'sku': 184242, 'barcode': '002516SH', 'reference': '002516SH', 'reference2': '002516SH',
                                'description': 'iPhone SE 3 128GB Midnight EUS (Shiny)', 'warehouse_id': 1,
                                'weight': 630, 'dimensions': {'length': 210, 'width': 144, 'height': 70},
                                'items_in_box': 1, 'level': 0, 'atp': 0, 'master_level': 0, 'master_atp': 0,
                                'status': 1, 'status_string': 'on', 'lot_number': '', 'tht_alert': 'none',
                                'tht_date': False, 'tht_minimum': False,
                                'last_update': {'date': '2023-05-23 07:18:23', 'timezone_type': 3,
                                                'timezone': 'Europe/Brussels'},
                                'last_atp_update': {'date': '2023-05-23 07:18:23', 'timezone_type': 3,
                                                    'timezone': 'Europe/Brussels'}},
                     '198450': {'sku': 198450, 'barcode': '002516SH', 'reference': '002516SH', 'reference2': '002516SH',
                                'description': 'iPhone SE 3 128GB Midnight EUS (Shiny)', 'warehouse_id': 1,
                                'weight': 630, 'dimensions': {'length': 210, 'width': 144, 'height': 70},
                                'items_in_box': 1, 'level': 0, 'atp': 0, 'master_level': 0, 'master_atp': 0,
                                'status': 1, 'status_string': 'on', 'lot_number': '', 'tht_alert': 'none',
                                'tht_date': False, 'tht_minimum': False,
                                'last_update': {'date': '2023-05-23 07:18:23', 'timezone_type': 3,
                                                'timezone': 'Europe/Brussels'},
                                'last_atp_update': {'date': '2023-05-23 07:18:23', 'timezone_type': 3,
                                                    'timezone': 'Europe/Brussels'}},
                     '206507': {'sku': 206507, 'barcode': '002516SH', 'reference': '002516SH', 'reference2': '002516SH',
                                'description': 'iPhone SE 3 128GB Midnight EUS (Shiny)', 'warehouse_id': 1,
                                'weight': 630, 'dimensions': {'length': 210, 'width': 144, 'height': 70},
                                'items_in_box': 1, 'level': 0, 'atp': 0, 'master_level': 0, 'master_atp': 0,
                                'status': 1, 'status_string': 'on', 'lot_number': '', 'tht_alert': 'none',
                                'tht_date': False, 'tht_minimum': False,
                                'last_update': {'date': '2023-05-23 07:18:23', 'timezone_type': 3,
                                                'timezone': 'Europe/Brussels'},
                                'last_atp_update': {'date': '2023-05-23 07:18:23', 'timezone_type': 3,
                                                    'timezone': 'Europe/Brussels'}},
                     '211793': {'sku': 211793, 'barcode': '002516SH', 'reference': '002516SH', 'reference2': '002516SH',
                                'description': 'iPhone SE 3 128GB Midnight EUS (Shiny)', 'warehouse_id': 1,
                                'weight': 630, 'dimensions': {'length': 210, 'width': 144, 'height': 70},
                                'items_in_box': 1, 'level': 0, 'atp': 0, 'master_level': 0, 'master_atp': 0,
                                'status': 1, 'status_string': 'on', 'lot_number': '', 'tht_alert': 'none',
                                'tht_date': False, 'tht_minimum': False,
                                'last_update': {'date': '2023-05-23 07:18:23', 'timezone_type': 3,
                                                'timezone': 'Europe/Brussels'},
                                'last_atp_update': {'date': '2023-05-23 07:18:23', 'timezone_type': 3,
                                                    'timezone': 'Europe/Brussels'}}}
        sku = "002516SH"
        actual, _, _ = getStockFromItems(test_resp.items(), sku)
        self.assertEqual(actual, False)

    def test_stock_check_calculation_returns_non_zero(self):
        test_resp = {'144290': {'sku': 144290, 'barcode': '002516SH', 'reference': '002516SH', 'reference2': '002516SH',
                                'description': 'iPhone SE 3 128GB Midnight EUS (Shiny)', 'warehouse_id': 1,
                                'weight': 630, 'dimensions': {'length': 210, 'width': 144, 'height': 70},
                                'items_in_box': 1, 'level': 0, 'atp': 2, 'master_level': 0, 'master_atp': 0,
                                'status': 1, 'status_string': 'on', 'lot_number': '', 'tht_alert': 'none',
                                'tht_date': False, 'tht_minimum': False,
                                'last_update': {'date': '2023-05-23 07:18:23', 'timezone_type': 3,
                                                'timezone': 'Europe/Brussels'},
                                'last_atp_update': {'date': '2023-05-23 07:18:23', 'timezone_type': 3,
                                                    'timezone': 'Europe/Brussels'}},
                     '184242': {'sku': 184242, 'barcode': '002516SH', 'reference': '002516SH', 'reference2': '002516SH',
                                'description': 'iPhone SE 3 128GB Midnight EUS (Shiny)', 'warehouse_id': 1,
                                'weight': 630, 'dimensions': {'length': 210, 'width': 144, 'height': 70},
                                'items_in_box': 1, 'level': 0, 'atp': 0, 'master_level': 0, 'master_atp': 0,
                                'status': 1, 'status_string': 'on', 'lot_number': '', 'tht_alert': 'none',
                                'tht_date': False, 'tht_minimum': False,
                                'last_update': {'date': '2023-05-23 07:18:23', 'timezone_type': 3,
                                                'timezone': 'Europe/Brussels'},
                                'last_atp_update': {'date': '2023-05-23 07:18:23', 'timezone_type': 3,
                                                    'timezone': 'Europe/Brussels'}},
                     '198450': {'sku': 198450, 'barcode': '002516SH', 'reference': '002516SH', 'reference2': '002516SH',
                                'description': 'iPhone SE 3 128GB Midnight EUS (Shiny)', 'warehouse_id': 1,
                                'weight': 630, 'dimensions': {'length': 210, 'width': 144, 'height': 70},
                                'items_in_box': 1, 'level': 0, 'atp': 0, 'master_level': 0, 'master_atp': 0,
                                'status': 1, 'status_string': 'on', 'lot_number': '', 'tht_alert': 'none',
                                'tht_date': False, 'tht_minimum': False,
                                'last_update': {'date': '2023-05-23 07:18:23', 'timezone_type': 3,
                                                'timezone': 'Europe/Brussels'},
                                'last_atp_update': {'date': '2023-05-23 07:18:23', 'timezone_type': 3,
                                                    'timezone': 'Europe/Brussels'}},
                     '206507': {'sku': 206507, 'barcode': '002516SH', 'reference': '002516SH', 'reference2': '002516SH',
                                'description': 'iPhone SE 3 128GB Midnight EUS (Shiny)', 'warehouse_id': 1,
                                'weight': 630, 'dimensions': {'length': 210, 'width': 144, 'height': 70},
                                'items_in_box': 1, 'level': 0, 'atp': 1, 'master_level': 0, 'master_atp': 0,
                                'status': 1, 'status_string': 'on', 'lot_number': '', 'tht_alert': 'none',
                                'tht_date': False, 'tht_minimum': False,
                                'last_update': {'date': '2023-05-23 07:18:23', 'timezone_type': 3,
                                                'timezone': 'Europe/Brussels'},
                                'last_atp_update': {'date': '2023-05-23 07:18:23', 'timezone_type': 3,
                                                    'timezone': 'Europe/Brussels'}},
                     '211793': {'sku': 211793, 'barcode': '002516SH', 'reference': '002516SH', 'reference2': '002516SH',
                                'description': 'iPhone SE 3 128GB Midnight EUS (Shiny)', 'warehouse_id': 1,
                                'weight': 630, 'dimensions': {'length': 210, 'width': 144, 'height': 70},
                                'items_in_box': 1, 'level': 0, 'atp': 0, 'master_level': 0, 'master_atp': 0,
                                'status': 1, 'status_string': 'on', 'lot_number': '', 'tht_alert': 'none',
                                'tht_date': False, 'tht_minimum': False,
                                'last_update': {'date': '2023-05-23 07:18:23', 'timezone_type': 3,
                                                'timezone': 'Europe/Brussels'},
                                'last_atp_update': {'date': '2023-05-23 07:18:23', 'timezone_type': 3,
                                                    'timezone': 'Europe/Brussels'}}}
        sku = "002516SH"
        actual, _, _ = getStockFromItems(test_resp.items(), sku)
        self.assertEqual(actual, True)
