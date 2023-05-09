from core.marketplace_clients.bmclient import BackMarketClient
import unittest

from services.database_management.app.controller.utils.swd_utils import SWDShippingData


class TestBackmarketClient(unittest.TestCase):
    def test_generateItemsBodyForSWDCreateOrderRequestWithSamsung(self):
        Client = BackMarketClient()
        orderItems = [
            {
                "id": "5266756",
                "listing": "002346BR",
                "quantity": 1,
                "price": "775.12"
            },
        ]
        swdModelNames = ["Samsung Galaxy S10e 128GB Prism Black EUS (Shiny)"]

        actualValue = Client.generateItemsBodyForSWDCreateOrderRequest(orderItems=orderItems,
                                                                       swdModelNames=swdModelNames)
        expectedValue = [
            {
                "external_orderline_id": "5266756",
                "skuType": "reference",
                "sku": "002346BR",
                "amount": 1,
                "price": "775.12"
            },
            {
                "skuType": "reference",
                "sku": "002694",
                "amount": 1,
                "price": 2
            }
        ]
        self.assertCountEqual(expectedValue, actualValue)

    def test_generateItemsBodyForSWDCreateOrderRequestWithIPadPro(self):
        Client = BackMarketClient()
        orderItems = [
            {
                "id": "5266756",
                "listing": "002346BR",
                "quantity": 1,
                "price": "775.12"
            },
        ]
        swdModelNames = ["EUS iPad Pro"]

        actualValue = Client.generateItemsBodyForSWDCreateOrderRequest(orderItems=orderItems,
                                                                       swdModelNames=swdModelNames)
        expectedValue = [
            {
                "external_orderline_id": "5266756",
                "skuType": "reference",
                "sku": "002346BR",
                "amount": 1,
                "price": "775.12"
            },
            {
                "skuType": "reference",
                "sku": "002478",
                "amount": 1,
                "price": 2
            }
        ]
        self.assertCountEqual(expectedValue, actualValue)

    def test_generateItemsBodyForSWDCreateOrderRequestWithIPad6(self):
        Client = BackMarketClient()
        orderItems = [
            {
                "id": "5266756",
                "listing": "002346BR",
                "quantity": 1,
                "price": "775.12"
            },
        ]
        swdModelNames = ["EUS iPad 6"]

        actualValue = Client.generateItemsBodyForSWDCreateOrderRequest(orderItems=orderItems,
                                                                       swdModelNames=swdModelNames)
        expectedValue = [
            {
                "external_orderline_id": "5266756",
                "skuType": "reference",
                "sku": "002346BR",
                "amount": 1,
                "price": "775.12"
            },
            {
                "skuType": "reference",
                "sku": "002351",
                "amount": 1,
                "price": 2
            }
        ]
        self.assertCountEqual(expectedValue, actualValue)

    def test_generateItemsBodyForSWDCreateOrderRequestWithIPad7(self):
        Client = BackMarketClient()
        orderItems = [
            {
                "id": "5266756",
                "listing": "002346BR",
                "quantity": 1,
                "price": "775.12"
            },
        ]
        swdModelNames = ["EUS iPad 7"]

        actualValue = Client.generateItemsBodyForSWDCreateOrderRequest(orderItems=orderItems,
                                                                       swdModelNames=swdModelNames)
        expectedValue = [
            {
                "external_orderline_id": "5266756",
                "skuType": "reference",
                "sku": "002346BR",
                "amount": 1,
                "price": "775.12"
            },
            {
                "skuType": "reference",
                "sku": "002351",
                "amount": 1,
                "price": 2
            }
        ]
        self.assertCountEqual(expectedValue, actualValue)

    def test_generateItemsBodyForSWDCreateOrderRequestWithDifferentCables(self):
        Client = BackMarketClient()
        orderItems = [
            {
                "id": "5263756",
                "listing": "002346BR",
                "quantity": 1,
                "price": "775.12"
            },
            {
                "id": "6253764",
                "listing": "002336SL",
                "quantity": 1,
                "price": "750.12"
            },
        ]
        swdModelNames = ["EUS iPhone 11", "EUS iPhone 12"]

        actualValue = Client.generateItemsBodyForSWDCreateOrderRequest(orderItems=orderItems,
                                                                       swdModelNames=swdModelNames)
        expectedValue = [
            {
                "external_orderline_id": "5263756",
                "skuType": "reference",
                "sku": "002346BR",
                "amount": 1,
                "price": "775.12"
            },
            {
                "external_orderline_id": "6253764",
                "skuType": "reference",
                "sku": "002336SL",
                "amount": 1,
                "price": "750.12"
            },
            {
                "skuType": "reference",
                "sku": "002331",
                "amount": 1,
                "price": 2
            },
            {
                "skuType": "reference",
                "sku": "002204",
                "amount": 1,
                "price": 2
            },
            {
                "skuType": "barcode",
                "sku": "SKU_136666",
                "amount": 1,
                "price": 2
            }
        ]
        self.assertCountEqual(expectedValue, actualValue)

    def test_generateItemsBodyForSWDCreateOrderRequestWithSingleInfoSheetForMultipleIPhones(self):
        Client = BackMarketClient()
        orderItems = [
            {
                "id": "625382",
                "listing": "002346BR",
                "quantity": 1,
                "price": "775.12"
            },
            {
                "id": "782363",
                "listing": "002346BR",
                "quantity": 1,
                "price": "775.12"
            },
        ]
        swdModelNames = ["EUS iPhone 12", "EUS iPhone 12"]

        expectedValue = [
            {
                "external_orderline_id": "625382",
                "skuType": "reference",
                "sku": "002346BR",
                "amount": 1,
                "price": "775.12"
            },
            {
                "external_orderline_id": "782363",
                "skuType": "reference",
                "sku": "002346BR",
                "amount": 1,
                "price": "775.12"
            },
            {
                "skuType": "reference",
                "sku": "002331",
                "amount": 1,
                "price": 2
            },
            {
                "skuType": "reference",
                "sku": "002331",
                "amount": 1,
                "price": 2
            },
            {
                "skuType": "barcode",
                "sku": "SKU_136666",
                "amount": 1,
                "price": 2
            }
        ]

        actualValue = Client.generateItemsBodyForSWDCreateOrderRequest(orderItems=orderItems,
                                                                       swdModelNames=swdModelNames)
        self.assertCountEqual(expectedValue, actualValue)

    def test_getBodyForUpdateStateToShippedRequestWithSingleIMEI(self):
        c = BackMarketClient()
        shipping_data = SWDShippingData(
            order_id="26601104",
            item_id="26601198",
            sku="002378SH",
            serial_number="353018114641439",
            shipper="DHL",
            tracking_number="129493023",
            tracking_url='https://www.backmarket.fr/tracking/order?u=161400'
                         '8&orderNo=EU26387758&zip=75011&lang=fr&use_origin'
                         '_courier=true',
            is_multi_sku=False
        )
        resp = c.getBodyForUpdateStateToShippedRequest(shipping_data)
        expected_resp = {"order_id": "26601104",
                         "sku": "002378SH",
                         "new_state": 3,
                         "tracking_number": "129493023",
                         "tracking_url": 'https://www.backmarket.fr/tracking/order?u=1614008&orderNo=EU26387758&zip=75'
                                         '011&lang=fr&use_origin_courier=true',
                         "shipper": "DHL",
                         "imei": "353018114641439"}
        self.assertDictEqual(resp, expected_resp)

    def test_getBodyForUpdateStateToShippedRequestWithSingleSerialNumber(self):
        c = BackMarketClient()
        shipping_data = SWDShippingData(
            order_id="26601104",
            item_id="26601198",
            sku="002378SH",
            serial_number="353018DAE1",
            shipper="DHL",
            tracking_number="129493023",
            tracking_url='https://www.backmarket.fr/tracking/order?u=161400'
                         '8&orderNo=EU26387758&zip=75011&lang=fr&use_origin'
                         '_courier=true',
            is_multi_sku=False
        )
        resp = c.getBodyForUpdateStateToShippedRequest(shipping_data)
        expected_resp = {"order_id": "26601104",
                         "sku": "002378SH",
                         "new_state": 3,
                         "tracking_number": "129493023",
                         "tracking_url": 'https://www.backmarket.fr/tracking/order?u=1614008&orderNo=EU26387758&zip=75'
                                         '011&lang=fr&use_origin_courier=true',
                         "shipper": "DHL",
                         "serial_number": "353018DAE1"}
        self.assertDictEqual(resp, expected_resp)

    def test_getBodyForUpdateStateToShippedRequestWithMultipleSerialNumber(self):
        c = BackMarketClient()
        shipping_data = SWDShippingData(
            order_id="26601104",
            item_id="26601198",
            sku="002378SH",
            serial_number="353018DAE1",
            shipper="DHL",
            tracking_number="129493023",
            tracking_url='https://www.backmarket.fr/tracking/order?u=161400'
                         '8&orderNo=EU26387758&zip=75011&lang=fr&use_origin'
                         '_courier=true',
            is_multi_sku=True
        )
        resp = c.getBodyForUpdateStateToShippedRequest(shipping_data)
        expected_resp = {"order_id": "26601104",
                         "sku": "002378SH",
                         "new_state": 3,
                         "tracking_number": "129493023",
                         "tracking_url": 'https://www.backmarket.fr/tracking/order?u=1614008&orderNo=EU26387758&zip=75'
                                         '011&lang=fr&use_origin_courier=true',
                         "shipper": "DHL"}
        self.assertDictEqual(resp, expected_resp)

    def test_getBodyForUpdateStateToShippedRequestWithMultipleIMEIs(self):
        c = BackMarketClient()
        shipping_data = SWDShippingData(
            order_id="26601104",
            item_id="26601198",
            sku="002378SH",
            serial_number="353018114641439",
            shipper="DHL",
            tracking_number="129493023",
            tracking_url='https://www.backmarket.fr/tracking/order?u=161400'
                         '8&orderNo=EU26387758&zip=75011&lang=fr&use_origin'
                         '_courier=true',
            is_multi_sku=True
        )
        resp = c.getBodyForUpdateStateToShippedRequest(shipping_data)
        expected_resp = {"order_id": "26601104",
                         "sku": "002378SH",
                         "new_state": 3,
                         "tracking_number": "129493023",
                         "tracking_url": 'https://www.backmarket.fr/tracking/order?u=1614008&orderNo=EU26387758&zip=75'
                                         '011&lang=fr&use_origin_courier=true',
                         "shipper": "DHL"}
        self.assertDictEqual(resp, expected_resp)
