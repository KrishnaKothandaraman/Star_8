from core.marketplace_clients.bmclient import BackMarketClient
import unittest


class TestBackmarketClient(unittest.TestCase):
    def test_generateItemsBodyForSWDCreateOrderRequestWithIPad(self):
        Client = BackMarketClient()
        orderItems = [
            {
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

    def test_generateItemsBodyForSWDCreateOrderRequestWithDifferentCables(self):
        Client = BackMarketClient()
        orderItems = [
            {
                "listing": "002346BR",
                "quantity": 1,
                "price": "775.12"
            },
            {
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
                "skuType": "reference",
                "sku": "002346BR",
                "amount": 1,
                "price": "775.12"
            },
            {
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
                "listing": "002346BR",
                "quantity": 1,
                "price": "775.12"
            },
            {
                "listing": "002346BR",
                "quantity": 1,
                "price": "775.12"
            },
        ]
        swdModelNames = ["EUS iPhone 12", "EUS iPhone 12"]

        expectedValue = [
            {
                "skuType": "reference",
                "sku": "002346BR",
                "amount": 1,
                "price": "775.12"
            },
            {
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
