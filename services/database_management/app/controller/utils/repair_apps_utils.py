import enum
import json
import os
from typing import Optional, List

import requests
from dotenv import load_dotenv

from core.custom_exceptions.general_exceptions import GetStockFromRepairAppsFailedException, \
    StockAllocationFailedException, CreateOrderInRepairAppsFailedException, GetTrackingDataFromAppsheetFailedException
from core.marketplace_clients.clientinterface import MarketPlaceClient
from core.marketplace_clients.rfclient import RefurbedClient
from services.database_management.app.controller.utils import general_utils

load_dotenv()

AppSheetAccessKey = os.getenv("REPAIRAPPSACCESSKEY")
APPSHEET_TRACKING_URL = "https://api.appsheet.com/api/v2/apps/8a2d0562-676f-4945-8f5b-8fb7f28e93d6/tables/Tracking/Find"


class Source(enum.Enum):
    EUPurchase = 0
    Resale = 1

    def get_app_sheet_url_from_source(self, source):
        if source == self.EUPurchase:
            return "https://api.appsheet.com/api/v2/apps/8a2d0562-676f-4945-8f5b-8fb7f28e93d6/tables" \
                   "/EU_purchase_instock/find"
        else:
            return "https://api.appsheet.com/api/v2/apps/8a2d0562-676f-4945-8f5b-8fb7f28e93d6/tables" \
                   "/Reair%20EU%20LIST%20ON%20Sales/find"

    def get_add_order_url_from_source(self, source):
        if source == self.EUPurchase:
            return "https://api.appsheet.com/api/v2/apps/8a2d0562-676f-4945-8f5b-8fb7f28e93d6/tables" \
                   "/EU_purchase_Resales/add"
        else:
            return "https://api.appsheet.com/api/v2/apps/8a2d0562-676f-4945-8f5b-8fb7f28e93d6/tables" \
                   "/Resales%20List/add"


class StockCheckAvailabilityResult(enum.Enum):
    FULLY_AVAILABLE = 0
    PARTIALLY_AVAILABLE = 1
    NOT_AVAILABLE = 2


class StockCheckResult:
    imei_list: List[str]
    sku_list: List[str]
    availability_result: StockCheckAvailabilityResult

    def __init__(self, imei_list: List[str], availability_result: StockCheckAvailabilityResult, sku_list: List[str]):
        self.imei_list = imei_list
        self.availability_result = availability_result
        self.sku_list = sku_list


def get_stock_from_repair_apps(source: Source):
    url = source.get_app_sheet_url_from_source(source)
    headers = {
        "applicationAccessKey": AppSheetAccessKey
    }
    payload = {
        "Action": "Find",
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
        ]
    }
    resp = requests.post(url=url, headers=headers, json=payload)

    if resp.status_code != 200:
        raise GetStockFromRepairAppsFailedException("Failed to get stock from repair apps. Reason: %s" % resp.reason)
    return resp.json()


def get_imei_for_item(sku, stock_list, used_imeis: set) -> Optional[str]:
    for stock in stock_list:
        if stock["SKU"] == sku and stock["IMEI"] not in used_imeis:
            return stock["IMEI"]
    return None


def perform_stock_check_in_repair_app(client: MarketPlaceClient, items, source: Source) -> StockCheckResult:
    try:
        eu_purchase_stock = get_stock_from_repair_apps(source)
        item_imei_list = []
        sku_list = []
        used_imeis = set()
        """ TODO: loop through items and check stock. If so return True!"""
        for item in items:
            sku = client.getSku(item)
            item_imei = get_imei_for_item(sku, eu_purchase_stock, used_imeis)
            if item_imei:
                item_imei_list.append(item_imei)
                used_imeis.add(item_imei)
                sku_list.append(sku)

        if len(item_imei_list) == len(items):
            return StockCheckResult(item_imei_list, StockCheckAvailabilityResult.FULLY_AVAILABLE, sku_list)
        elif len(item_imei_list) > 0:
            return StockCheckResult(item_imei_list, StockCheckAvailabilityResult.PARTIALLY_AVAILABLE, sku_list)
        return StockCheckResult([], StockCheckAvailabilityResult.NOT_AVAILABLE, [])

    except GetStockFromRepairAppsFailedException as e:
        print(e.args[0])
    except Exception as e:
        print(f"Unknown Exception {e.args[0]}")


def create_order_in_repair_apps(formatted_order, stock_result: StockCheckResult, source: Source):
    """Formatted order follows schema in column_mapping.py"""
    url = source.get_add_order_url_from_source(source)

    headers = {
        "applicationAccessKey": AppSheetAccessKey
    }
    payload = {
        "Action": "Add",
        "Properties": {
            "Locale": "en-US",
            "Location": "47.623098, -122.330184",
            "Timezone": "Pacific Standard Time",
            "UserSettings": {
                "Option 1": "value1",
                "Option 2": "value2"
            }
        },
        "Rows": []
    }
    """
    the current system does not support multiple orders with the same order id. Therefore orders with multiple
    items will need the orderid to be of the form orderid, orderid-2, orderid-3, etc.
    Multiple orderlines have to also say "Multiple order" as fields for all non imei or order_id fields
    """
    order_id_addition = ""
    first_name, last_name, street, street2, postal_code, country, city, phone, email = \
        formatted_order["shipping_first_name"], formatted_order["shipping_last_name"], \
            formatted_order["shipping_address1"], formatted_order["shipping_address2"], \
            formatted_order["shipping_postal_code"], formatted_order["shipping_country_code"], \
            formatted_order["shipping_city"], formatted_order["shipping_phone_number"], \
            formatted_order["customer_email"]
    for i, (imei, sku) in enumerate(zip(stock_result.imei_list, stock_result.sku_list)):
        payload["Rows"].append({
            "IMEI": imei,
            "order_id": formatted_order["order_id"] + order_id_addition,
            "first_name": first_name,
            "last_name": last_name,
            "street": street,
            "street2": street2,
            "postal_code": postal_code,
            "country": country,
            "city": city,
            "phone": phone,
            "email": email
        })
        order_id_addition = f"-{i + 2}"
        first_name, last_name, street, street2, postal_code, country, city, phone, email = \
            "Multiple order", "Multiple order", "Multiple order", "Multiple order", "Multiple order", \
            "Multiple order", "Multiple order", "Multiple order", "Multiple order"
    resp = requests.post(url=url, headers=headers, json=payload)
    if resp.status_code != 200:
        raise CreateOrderInRepairAppsFailedException("Failed to create order in repair apps. Reason: %s" % resp.reason)
    print(resp.status_code)


def allocate_stock_for_order_items(client: MarketPlaceClient, order):
    order_items = client.getOrderItems(order)
    formatted_order = client.convertOrderToSheetColumns(order)[0]
    formatted_order["shipper"] = general_utils.getShipperName(price=float(formatted_order["total_charged"]),
                                                              chosenShipperName=formatted_order["shipper"],
                                                              country_code=formatted_order["shipping_country_code"])

    print(f"Order id: {formatted_order['order_id']}")
    eu_purchase_result = perform_stock_check_in_repair_app(client, order_items, Source.EUPurchase)
    if eu_purchase_result.availability_result == StockCheckAvailabilityResult.FULLY_AVAILABLE:
        print("Fully available")
        create_order_in_repair_apps(formatted_order, eu_purchase_result, Source.EUPurchase)

    elif eu_purchase_result.availability_result == StockCheckAvailabilityResult.PARTIALLY_AVAILABLE:
        print("Partially available in Eu Purchase")
        in_stock_items = [item for item in order_items if item[client.skuFieldName] not in eu_purchase_result.sku_list]
        resale_instock_result = perform_stock_check_in_repair_app(client, in_stock_items, Source.Resale)

        if resale_instock_result.availability_result != StockCheckAvailabilityResult.FULLY_AVAILABLE:
            print("Unavailable in both")
            raise StockAllocationFailedException("Failed to allocate stock for order items")
        print("Partially available in Resale")
        create_order_in_repair_apps(formatted_order, eu_purchase_result, Source.EUPurchase)
        create_order_in_repair_apps(formatted_order, resale_instock_result, Source.Resale)
    else:
        resale_instock_result = perform_stock_check_in_repair_app(client, order_items, Source.Resale)
        if resale_instock_result.availability_result != StockCheckAvailabilityResult.FULLY_AVAILABLE:
            print("Unavailable in both")
            raise StockAllocationFailedException("Failed to allocate stock for order items")
        print("Resale fully available")

        create_order_in_repair_apps(formatted_order, resale_instock_result, Source.Resale)


def get_tracking_data_from_appsheet(orderID: str):
    payload = {
        "Action": "Find",
        "Properties": {
            "Locale": "en-US",
            "Location": "47.623098, -122.330184",
            "Timezone": "Pacific Standard Time",
            "UserSettings": {
                "Option 1": "value1",
                "Option 2": "value2"
            }
        },
        "Rows": [{
            "order_id": orderID
        }]
    }
    headers = {
        "applicationAccessKey": AppSheetAccessKey
    }
    resp = requests.post(url=APPSHEET_TRACKING_URL, headers=headers, json=payload)
    if resp.status_code != 200:
        raise GetTrackingDataFromAppsheetFailedException("Failed to get tracking data from appsheet."
                                                         " Reason: %s" % resp.reason)
    if len(resp.json()) == 0:
        raise GetTrackingDataFromAppsheetFailedException("Order not shipped yet")
    return resp.json()[0]