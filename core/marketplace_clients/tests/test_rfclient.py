from core.marketplace_clients.rfclient import RefurbedClient
import unittest


class TestRefurbedClient(unittest.TestCase):

    def test_generateItemsBodyForSWDCreateOrderRequestWithIPad(self):
        Client = RefurbedClient()
        orderItems = [
            {
                "sku": "002346BR",
                "settlement_total_charged": "775.12"
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
        Client = RefurbedClient()
        orderItems = [
            {
                "sku": "002346BR",
                "settlement_total_charged": "775.12"
            },
            {
                "sku": "002336SL",
                "settlement_total_charged": "750.12"
            },
        ]
        swdModelNames = ["EUS iPhone 11", "EUS iPhone 12"]

        swdBody = Client.generateItemsBodyForSWDCreateOrderRequest(orderItems=orderItems,
                                                                   swdModelNames=swdModelNames)
        expectedBody = [
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
        ]
        self.assertCountEqual(swdBody, expectedBody)

    def test_generateItemsBodyForSWDCreateOrderRequestWithSingleInfoSheetForMultipleIPhones(self):
        Client = RefurbedClient()
        orderItems = [
            {
                "sku": "002346BR",
                "settlement_total_charged": "775.12"
            },
            {
                "sku": "002346BR",
                "settlement_total_charged": "775.12"
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
        ]

        actualValue = Client.generateItemsBodyForSWDCreateOrderRequest(orderItems=orderItems,
                                                                       swdModelNames=swdModelNames)
        self.assertCountEqual(expectedValue, actualValue)