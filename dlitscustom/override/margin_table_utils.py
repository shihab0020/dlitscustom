import frappe
import json


@frappe.whitelist()
def get_item_costs(item_codes):
    """
    Return cost and stock info for a list of item codes.
    Cost logic:
      Stock items:     max(last_purchase_rate, custom_rfq_price)  — whichever is higher
      Non-stock items: caller applies 75% of rate as default cost
    """
    if isinstance(item_codes, str):
        item_codes = json.loads(item_codes)

    if not item_codes:
        return {}

    rows = frappe.get_all(
        "Item",
        filters={"name": ["in", item_codes]},
        fields=["name", "last_purchase_rate", "custom_rfq_price", "is_stock_item"],
    )

    result = {}
    for r in rows:
        lpr = float(r.last_purchase_rate or 0)
        rfq = float(r.custom_rfq_price or 0)
        cost = max(lpr, rfq)
        result[r.name] = {
            "cost":         cost,
            "is_stock_item": int(r.is_stock_item or 0),
        }

    return result
