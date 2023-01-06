columnMapping = {
    "global": {
        "order_id": {
            "BackMarket": "order_id",
            "Refurbed": "id",
        },
        "Market":{
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
            "Refurbed": "invoice_address/email",
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
            "Refurbed": "shipping_address/company",
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
        "shipper": {
            "BackMarket": "shipper",
            "Refurbed": None
        },
        "tracking_url": {
            "BackMarket": "tracking_url",
            "Refurbed": "parcel_tracking_url"
        },
        "tracking_number": {
            "BackMarket": "item_identifier",
            "Refurbed": "tracking_number"
        },
        "payment_method": {
            "BackMarket": "payment_method",
            "Refurbed": None
        },
        "sales_taxes": {
            "BackMarket": "sales_taxes",
            "Refurbed": None
        },
        "expected_dispatch_date": {
            "BackMarket": "expected_dispatch_date",
            "Refurbed": None
        },
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
        "item_state": {
            "BackMarket": "state",
            "Refurbed": "state"
        },
        "sku": {
            "BackMarket": "listing",
            "Refurbed": "sku"
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
            "Refurbed": None
        },
    }
}
