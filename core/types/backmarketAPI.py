import enum


class BackMarketOrderStates(enum.Enum):
    New = 0
    Pending_Payment = 10
    Accept = 1
    Pending_Shipment = 3
    Payment_Failed = 8
    Shipped = 9

    @staticmethod
    def getStrFromEnum(val):
        return {
            0: "NEW", 10: "PENDING PAYMENT", 1: "ACCEPTED", 3: "PENDING SHIPMENT", 8: "PAYMENT FAILED", 9: "SHIPPED"
        }[val]


class BackMarketGender(enum.Enum):
    Male = 0
    Female = 1

    @staticmethod
    def getStrFromEnum(val):
        return {
            0: "MALE", 1: "FEMALE"}[val]


class BackMarketOrderlinesStates(enum.Enum):
    New = 0
    Validate_Orderline = 1
    Order_Accepted = 2
    Shipped = 3
    Cancelled = 4
    Refund_Before_Shipping = 5
    Refund_After_Shipping = 6
    Payment_Failed = 7
    Awaiting_Payment = 8

    @staticmethod
    def getStrFromEnum(val):
        return {
            0: "NEW", 1: "VALIDATE ORDERLINE", 2: "ORDER ACCEPTED", 3: "SHIPPED", 4: "CANCELLED",
            5: "REFUND BEFORE SHIPPING", 6: "REFUND AFTER SHIPPING", 7: "PAYMENT FAILED", 8: "AWAITING PAYMENT"
        }[val]


#############
# Constants #
#############

BMDateStringFormat = "%Y-%m-%dT%H:%M:%S%z"
BMDateFieldName = "date_creation"
BMItemKeyName = "orderlines"
BMSKUFieldName = "listing"
BMOrderIDFieldName = "order_id"