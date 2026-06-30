import frappe
from dlitscustom.utils.get_pricing_rule_dlits import get_pricing_rule_dlits


def pricing_rule_verify_dlits(doc, method=None):
    """Validate item rates. Non-stock items: only block zero price.
    Stock items: check valuation rate, last purchase rate, and pricing rules."""
    if doc.get("is_return"):
        return

    is_allowed = "Shb Allow Below Price" in frappe.get_roles()

    errors = []
    customer   = doc.get("customer")
    price_list = doc.get("price_list") or doc.get("selling_price_list")

    for row in doc.get("items") or []:
        item_code = row.get("item_code")
        rate      = row.get("rate")
        if not item_code or rate is None:
            continue

        uom               = row.get("uom")
        conversion_factor = float(row.get("conversion_factor") or 1.0)

        item_master = frappe.db.get_value(
            "Item", item_code,
            ["valuation_rate", "last_purchase_rate", "is_stock_item"],
            as_dict=True,
        ) or {}

        if not cint(item_master.get("is_stock_item")):
            # Non-stock / service item: only block zero price, allow any other rate
            if not rate:
                errors.append(f"Item {frappe.bold(item_code)}: Price cannot be zero.")

        else:
            # Stock item: apply full cost checks
            item_valuation_rate = float(item_master.get("valuation_rate") or 0) * conversion_factor
            last_purchase_rate  = float(item_master.get("last_purchase_rate") or 0) * conversion_factor

            if not item_valuation_rate:
                errors.append(
                    f"Item {frappe.bold(item_code)}: Valuation Rate is zero or not set. "
                    f"Receive the item into stock before creating this document."
                )
                continue

            if not rate:
                errors.append(f"Item {frappe.bold(item_code)}: Price cannot be zero.")
                continue

            rule_price = get_pricing_rule_dlits(item_code, customer, price_list,
                                                uom=uom, conversion_factor=conversion_factor)
            if rule_price is not None and round(rate, 2) < round(rule_price, 2):
                errors.append(
                    f"Item {frappe.bold(item_code)}: Price ({rate}) is below "
                    f"Pricing Rule ({round(rule_price, 2)})."
                )

            if last_purchase_rate and rate < last_purchase_rate:
                errors.append(
                    f"Item {frappe.bold(item_code)}: Price ({rate}) is below "
                    f"Last Purchase Rate ({last_purchase_rate})."
                )

            if rate < item_valuation_rate:
                errors.append(
                    f"Item {frappe.bold(item_code)}: Price ({rate}) is below "
                    f"Valuation Rate ({item_valuation_rate})."
                )

    if not errors:
        return

    if is_allowed:
        frappe.msgprint("<br>".join(errors), title="Pricing Rule Warnings", indicator="orange")
    else:
        frappe.throw("<br>".join(errors), title="Pricing Rule Verification Failed")


def cint(value):
    try:
        return int(value or 0)
    except (ValueError, TypeError):
        return 0
