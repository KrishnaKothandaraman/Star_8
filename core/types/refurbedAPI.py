from typing import Literal, Dict

RFItemKeyName = "items"
RFDateFieldName = "released_at"
RFDateStringFormat = "%Y-%m-%dT%H:%M:%S.%fZ"
RFSKUFieldName = "listing"
RFOrderIDFieldName = "order_id"

OrderStates = Literal["NEW", "REJECTED", "CANCELLED", "ACCEPTED", "SHIPPED", "RETURNED"]

ShippingProfileID = Literal["754", "1001"]
ShipperName = Literal["UPS", "DHL Express"]

ShippingProfileIDMapping: Dict[str, ShipperName] = {
    "754": "UPS",
    "1001": "DHL Express"
}
