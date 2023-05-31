from core.marketplace_clients.rfclient import RefurbedClient
import unittest


class TestRefurbedClient(unittest.TestCase):

    def test_generateItemsBodyForSWDCreateOrderRequestWithIPadPro(self):
        Client = RefurbedClient()
        orderItems = [
            {
                "id": "12345754",
                "sku": "002346BR",
                "settlement_total_charged": "775.12"
            },
        ]
        swdModelNames = ["EUS iPad Pro"]

        actualValue = Client.generateItemsBodyForSWDCreateOrderRequest(orderItems=orderItems,
                                                                       swdModelNames=swdModelNames)
        expectedValue = [
            {
                "external_orderline_id": "12345754",
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

    def test_generateItemsBodyForSWDCreateOrderRequestWithIPadProLowerCase(self):
        Client = RefurbedClient()
        orderItems = [
            {
                "id": "12345754",
                "sku": "002346BR",
                "settlement_total_charged": "775.12"
            },
        ]
        swdModelNames = ["EUS ipad pro"]

        actualValue = Client.generateItemsBodyForSWDCreateOrderRequest(orderItems=orderItems,
                                                                       swdModelNames=swdModelNames)
        expectedValue = [
            {
                "external_orderline_id": "12345754",
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
        Client = RefurbedClient()
        orderItems = [
            {
                "id": "12345754",
                "sku": "002346BR",
                "settlement_total_charged": "775.12"
            },
        ]
        swdModelNames = ["EUS iPad 6"]

        actualValue = Client.generateItemsBodyForSWDCreateOrderRequest(orderItems=orderItems,
                                                                       swdModelNames=swdModelNames)
        expectedValue = [
            {
                "external_orderline_id": "12345754",
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

    def test_generateItemsBodyForSWDCreateOrderRequestWithIPad6LowerCase(self):
        Client = RefurbedClient()
        orderItems = [
            {
                "id": "12345754",
                "sku": "002346BR",
                "settlement_total_charged": "775.12"
            },
        ]
        swdModelNames = ["EUS ipad 6"]

        actualValue = Client.generateItemsBodyForSWDCreateOrderRequest(orderItems=orderItems,
                                                                       swdModelNames=swdModelNames)
        expectedValue = [
            {
                "external_orderline_id": "12345754",
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
        Client = RefurbedClient()
        orderItems = [
            {
                "id": "12345754",
                "sku": "002346BR",
                "settlement_total_charged": "775.12"
            },
        ]
        swdModelNames = ["EUS iPad 7"]

        actualValue = Client.generateItemsBodyForSWDCreateOrderRequest(orderItems=orderItems,
                                                                       swdModelNames=swdModelNames)
        expectedValue = [
            {
                "external_orderline_id": "12345754",
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

    def test_generateItemsBodyForSWDCreateOrderRequestWithIPad7LowerCase(self):
        Client = RefurbedClient()
        orderItems = [
            {
                "id": "12345754",
                "sku": "002346BR",
                "settlement_total_charged": "775.12"
            },
        ]
        swdModelNames = ["EUS ipad 7"]

        actualValue = Client.generateItemsBodyForSWDCreateOrderRequest(orderItems=orderItems,
                                                                       swdModelNames=swdModelNames)
        expectedValue = [
            {
                "external_orderline_id": "12345754",
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

    def test_generateItemsBodyForSWDCreateOrderRequestWithSamsung(self):
        Client = RefurbedClient()
        orderItems = [
            {
                "id": "12345754",
                "sku": "002346BR",
                "settlement_total_charged": "775.12"
            }
        ]
        swdModelNames = ["Samsung Galaxy S10e 128GB Prism Black EUS (Shiny)"]

        actualValue = Client.generateItemsBodyForSWDCreateOrderRequest(orderItems=orderItems,
                                                                       swdModelNames=swdModelNames)
        expectedValue = [
            {
                "external_orderline_id": "12345754",
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

    def test_generateItemsBodyForSWDCreateOrderRequestWithSamsungLowerCase(self):
        Client = RefurbedClient()
        orderItems = [
            {
                "id": "12345754",
                "sku": "002346BR",
                "settlement_total_charged": "775.12"
            }
        ]
        swdModelNames = ["samsung galaxy S10e 128GB Prism Black EUS (Shiny)"]

        actualValue = Client.generateItemsBodyForSWDCreateOrderRequest(orderItems=orderItems,
                                                                       swdModelNames=swdModelNames)
        expectedValue = [
            {
                "external_orderline_id": "12345754",
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

    def test_generateItemsBodyForSWDCreateOrderRequestWithDifferentCables(self):
        Client = RefurbedClient()
        orderItems = [
            {
                "id": "102934879",
                "sku": "002346BR",
                "settlement_total_charged": "775.12"
            },
            {
                "id": "102934279",
                "sku": "002336SL",
                "settlement_total_charged": "750.12"
            },
        ]
        swdModelNames = ["EUS iPhone 11", "EUS iPhone 12"]

        swdBody = Client.generateItemsBodyForSWDCreateOrderRequest(orderItems=orderItems,
                                                                   swdModelNames=swdModelNames)
        expectedBody = [
            {
                "external_orderline_id": "102934879",
                "skuType": "reference",
                "sku": "002346BR",
                "amount": 1,
                "price": "775.12"
            },
            {
                "external_orderline_id": "102934279",
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
        ]
        self.assertCountEqual(swdBody, expectedBody)

    def test_generateItemsBodyForSWDCreateOrderRequestWithSingleInfoSheetForMultipleIPhones(self):
        Client = RefurbedClient()
        orderItems = [
            {
                "id": "102934879",
                "sku": "002346BR",
                "settlement_total_charged": "775.12"
            },
            {
                "id": "109934879",
                "sku": "002346BR",
                "settlement_total_charged": "775.12"
            },
        ]
        swdModelNames = ["EUS iPhone 12", "EUS iPhone 12"]

        expectedValue = [
            {
                "external_orderline_id": "102934879",
                "skuType": "reference",
                "sku": "002346BR",
                "amount": 1,
                "price": "775.12"
            },
            {
                "external_orderline_id": "109934879",
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
        ]

        actualValue = Client.generateItemsBodyForSWDCreateOrderRequest(orderItems=orderItems,
                                                                       swdModelNames=swdModelNames)
        self.assertCountEqual(expectedValue, actualValue)

    @unittest.skip("Yet to implement")
    def test_getBodyForUpdateStateToShippedRequestWithOneItem(self):
        Client = RefurbedClient()
        items = {'sku': 182647, 'name': 'iPhone 13 Mini 128GB White EUS (Silver)', 'amount': 1,
                 'external_orderline_id': False,
                 'external_product_id': False, 'external_product_variant_id': False, 'comment': False,
                 'lot_number': False,
                 'tht_date': False, 'picked': True,
                 'product': {'stockId': '182647', 'barcode': '002661SL', 'reference': '002661SL',
                             'name': 'iPhone 13 Mini 128GB White EUS (Silver)', 'shopId': '11025',
                             'location': 'BIN001455_C4000487', 'level': '9', 'atp': '9', 'productsStockItemsInBox': '1',
                             'productsStockRegisterSerialNumber': '0', 'productsStockBreakable': '0'},
                 'serialnumber': ['352922180292491']}
