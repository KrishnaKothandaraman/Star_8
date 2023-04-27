import dataclasses
import datetime
import enum
from typing import List


class BuyBoxState(enum.Enum):
    INELIGIBLE = enum.auto()
    ELIGIBLE = enum.auto()
    WON = enum.auto()


@dataclasses.dataclass
class BuyBoxInfo:
    buybox_state: BuyBoxState = None
    buybox_suggested_price: float = 0.0
    buybox_market_price: float = 0.0

    def get_buybox_state_as_str(self):
        return self.buybox_state.name

    def set_buy_box_state(self, buybox_state):
        if buybox_state == "ELIGIBLE":
            self.buybox_state = BuyBoxState.ELIGIBLE
        elif buybox_state == "WON":
            self.buybox_state = BuyBoxState.WON
        else:
            raise Exception(f"BuyBox State not set {buybox_state}")


class FieldType(enum.Enum):
    normal = enum.auto()
    dropdown = enum.auto()


@dataclasses.dataclass
class CellData:
    value: str
    field_type: FieldType
    field_values: List[str]

    def __init__(self, value, field_type, field_values):
        self.value = value
        self.field_type = field_type
        self.field_values = field_values


@dataclasses.dataclass
class ListingData:
    row_num: int
    title: str
    bm_quantity: int
    rf_quantity: int
    bm_listing_id: str
    rf_listing_id: str
    bm_listing_price: str
    rf_listing_price: str
    bm_min_price: str
    rf_min_price: str
    update_time: str
    rf_buyBoxInfo: BuyBoxInfo

    def __init__(self, row_num):
        self.row_num = row_num
        self.bm_listing_id = ""
        self.title = ""
        self.bm_quantity = 0
        self.rf_quantity = 0
        self.rf_listing_id = ""
        self.bm_listing_price = ""
        self.bm_min_price = ""
        self.rf_listing_price = ""
        self.rf_min_price = ""
        self.update_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.rf_buyBoxInfo = BuyBoxInfo()

    def set_rf_buybox_info(self, rf_listing):
        germanBuyBoxInfo = next(
            (market for market in rf_listing["offer"]["set_market_prices"] if market["market_code"] == "de"),
            None)
        if not germanBuyBoxInfo or germanBuyBoxInfo["instance_buybox_state"] == "INELIGIBLE":
            self.rf_buyBoxInfo.buybox_state = BuyBoxState.INELIGIBLE
        else:
            self.rf_buyBoxInfo.set_buy_box_state(germanBuyBoxInfo["instance_buybox_state"])
            if self.rf_buyBoxInfo.buybox_state != BuyBoxState.WON:
                self.rf_buyBoxInfo.buybox_suggested_price = germanBuyBoxInfo["instance_buybox_info"][
                    "suggested_offer_price"]
                self.rf_buyBoxInfo.buybox_market_price = germanBuyBoxInfo["instance_buybox_info"][
                    "site_market_competitor_price"]

    def get_total_quantity(self) -> int:
        return self.bm_quantity + self.rf_quantity

    def get_update_sheet_data(self):
        return [
            CellData(self.title, FieldType.normal, []),
            CellData(self.get_total_quantity(), FieldType.normal, []),
            CellData(self.bm_quantity, FieldType.normal, []),
            CellData(self.rf_quantity, FieldType.normal, []),
            CellData(self.update_time, FieldType.normal, []),
            CellData(self.bm_min_price, FieldType.normal, []),
            CellData(self.bm_listing_price, FieldType.normal, []),
            CellData(self.rf_min_price, FieldType.normal, []),
            CellData(self.rf_listing_price, FieldType.normal, []),
            CellData(self.rf_buyBoxInfo.get_buybox_state_as_str(), FieldType.normal, []),
            CellData(self.rf_buyBoxInfo.buybox_market_price, FieldType.normal, []),
            CellData(self.rf_buyBoxInfo.buybox_suggested_price, FieldType.normal, []),
            CellData("No", FieldType.dropdown, ["Yes", "No"])
        ]
