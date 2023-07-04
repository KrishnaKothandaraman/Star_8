"""
Each key in the dict represents a column in the google sheet.
The value for each key represents the corresponding json key from each marketplace
Global: These represent per order fields
Items: These represent per item fields. An order may consist of one or more items
NOTATIONS:
<val>: This denotes a constant value. If the parser encounters this format, it will use the value within <> as a constant
/ : The forward slash operator denotes a key from a nester json object. Cannot be used in conjunction with +
+ : The plus operator denotes joining of multiple column values. THIS ONLY WORKS IF THE JOINED COLUMNS ARE THE LAST IN
../ : Some per item fields may actually be global. In that case, prefix the mapping with this symbol to get from global
    fields in order json
THE HIERARCHY of / operators.
"""
columnMapping = {
    "global": {
        "order_id": {
            "BackMarket": "order_id",
            "Refurbed": "id",
        },
        "Market": {
            "BackMarket": "<BackMarket>",
            "Refurbed": "<Refurbed>"
        },
        "state": {
            "BackMarket": "state",
            "Refurbed": "state",
        },
        "notes": {
            "BackMarket": None,
            "Refurbed": "labels",
        },
        "customer_email": {
            "BackMarket": "shipping_address/email",
            "Refurbed": "customer_email",
        },
        "shipping_first_name": {
            "BackMarket": "shipping_address/first_name",
            "Refurbed": "shipping_address/first_name",
        },
        "shipping_last_name": {
            "BackMarket": "shipping_address/last_name",
            "Refurbed": "shipping_address/family_name",
        },
        "shipping_gender": {
            "BackMarket": "shipping_address/gender",
            "Refurbed": "shipping_address/entity",
        },
        "shipping_address1": {
            "BackMarket": "shipping_address/street",
            "Refurbed": "shipping_address/street_name",
        },
        "shipping_address2": {
            "BackMarket": "shipping_address/street2",
            "Refurbed": "shipping_address/house_no",
        },
        "shipping_postal_code": {
            "BackMarket": "shipping_address/postal_code",
            "Refurbed": "shipping_address/post_code",
        },
        "shipping_country_code": {
            "BackMarket": "shipping_address/country",
            "Refurbed": "shipping_address/country_code",
        },
        "shipping_city": {
            "BackMarket": "shipping_address/city",
            "Refurbed": "shipping_address/town",
        },
        "shipping_phone_number": {
            "BackMarket": "shipping_address/phone",
            "Refurbed": "shipping_address/phone_number",
        },
        "billing_first_name": {
            "BackMarket": "billing_address/first_name",
            "Refurbed": "invoice_address/first_name",
        },
        "billing_last_name": {
            "BackMarket": "billing_address/last_name",
            "Refurbed": "invoice_address/family_name",
        },
        "billing_gender": {
            "BackMarket": "billing_address/gender",
            "Refurbed": "invoice_address/entity",
        },
        "billing_address1": {
            "BackMarket": "billing_address/street",
            "Refurbed": "invoice_address/street_name",
        },
        "billing_address2": {
            "BackMarket": "billing_address/street2",
            "Refurbed": "invoice_address/house_no",
        },
        "billing_postal_code": {
            "BackMarket": "billing_address/postal_code",
            "Refurbed": "invoice_address/post_code",
        },
        "billing_country_code": {
            "BackMarket": "billing_address/country",
            "Refurbed": "invoice_address/country_code",
        },
        "billing_city": {
            "BackMarket": "billing_address/city",
            "Refurbed": "invoice_address/town",
        },
        "billing_phone_number": {
            "BackMarket": "billing_address/phone",
            "Refurbed": "invoice_address/phone_number",
        },
        "company": {
            "BackMarket": "shipping_address/company",
            "Refurbed": "invoice_address/company_name",
        },
        "currency": {
            "BackMarket": "currency",
            "Refurbed": "currency_code",
        },
        "paypal_reference": {
            "BackMarket": "paypal_reference",
            "Refurbed": None,
        },
        "psp_reference": {
            "BackMarket": "psp_reference",
            "Refurbed": None,
        },
        "installment_payment": {
            "BackMarket": "installment_payment",
            "Refurbed": None,
        },
        "date_creation": {
            "BackMarket": "date_creation",
            "Refurbed": "released_at"
        },
        "date_modification": {
            "BackMarket": "date_modification",
            "Refurbed": None,
        },
        "date_shipment": {
            "BackMarket": "date_shipping",
            "Refurbed": None,
        },
        "date_payment": {
            "BackMarket": "date_payment",
            "Refurbed": None,
        },
        "total_charged": {
            "BackMarket": "price",
            "Refurbed": "settlement_total_charged",
        },
        "is_refundable": {
            "BackMarket": None,
            "Refurbed": "is_refundable",
        },
        "is_invoicable": {
            "BackMarket": None,
            "Refurbed": "is_invoicable",
        },
        "has_invoice": {
            "BackMarket": None,
            "Refurbed": "has_invoicable",
        },
        "tracking_number": {
            "BackMarket": "tracking_number",
            "Refurbed": None
        },
        "payment_method": {
            "BackMarket": "payment_method",
            "Refurbed": None
        },
        "sales_taxes": {
            "BackMarket": "sales_taxes",
            "Refurbed": "<0.00>"
        },
        "expected_dispatch_date": {
            "BackMarket": "expected_dispatch_date",
            "Refurbed": None
        },
        "discount": {
            "BackMarket": None,
            "Refurbed": "total_discount"
        },
        "vat_number": {
            "BackMarket": None,
            "Refurbed": "invoice_address/company_vatin"
        }
    },
    "items": {
        "item_id": {
            "BackMarket": "id",
            "Refurbed": "id"
        },
        "item_name": {
            "BackMarket": "product",
            "Refurbed": "name"
        },
        "item_identifier": {
            "BackMarket": "imei+serial_number",
            "Refurbed": "item_identifier"
        },
        "tracking_url": {
            "BackMarket": "../tracking_url",
            "Refurbed": "parcel_tracking_url"
        },
        "item_state": {
            "BackMarket": "state",
            "Refurbed": "state"
        },
        "sku": {
            "BackMarket": "listing",
            "Refurbed": "sku"
        },
        "shipper": {
            "BackMarket": "../shipper",
            "Refurbed": "offer_data/shipping_profile_id"
        },
        "item_price": {
            "BackMarket": "price",
            "Refurbed": "settlement_total_charged"
        },
        "return_reason": {
            "BackMarket": "return_reason",
            "Refurbed": None
        },
        "return_message": {
            "BackMarket": "return_message",
            "Refurbed": None
        },
        "quantity": {
            "BackMarket": "quantity",
            "Refurbed": "<1>"
        },
        "settlement_total_commission": {
            "BackMarket": None,
            "Refurbed": "settlement_total_commission"
        },
        "settlement_base_commission": {
            "BackMarket": None,
            "Refurbed": "settlement_base_commission"
        },
        "settlement_payout_commission": {
            "BackMarket": None,
            "Refurbed": "settlement_payout_commission"
        },
        "settlement_dynamic_commission": {
            "BackMarket": None,
            "Refurbed": "settlement_dynamic_commission"
        },
        "shipping_price": {
            "BackMarket": "shipping_price",
            "Refurbed": "<0.00>"
        },
    }
}
