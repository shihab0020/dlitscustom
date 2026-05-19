import frappe
from dlitscustom.utils.get_pricing_rule_dlits import get_pricing_rule_dlits


def pricing_rule_verify_dlits(doc, method=None):
    """Validate that every item's rate meets the pricing rule floor."""
    allowed_roles = ["Shb Allow Below Price"]
    is_allowed = any(r in allowed_roles for r in frappe.get_roles(frappe.session.user))

    errors = []
    customer = doc.get("customer")
    price_list = doc.get("price_list") or doc.get("selling_price_list")

    for row in doc.get("items") or []:
        item_code = row.get("item_code")
        rate = row.get("rate")

        if not item_code or rate is None:
            continue

        uom = row.get("uom")
        conversion_factor = float(row.get("conversion_factor") or 1.0)

        item_master = frappe.db.get_value(
            "Item", item_code,
            ["valuation_rate", "last_purchase_rate"],
            as_dict=True,
        ) or {}
        # valuation_rate and last_purchase_rate are in stock UOM — scale to transaction UOM
        item_valuation_rate = float(item_master.get("valuation_rate") or 0) * conversion_factor
        last_purchase_rate = float(item_master.get("last_purchase_rate") or 0) * conversion_factor

        # E. Both cost references are zero — cannot verify
        if not item_valuation_rate and not last_purchase_rate:
            errors.append(
                f"Item {frappe.bold(item_code)}: Both Valuation Rate and Last Purchase Rate are zero. "
                f"Cannot proceed without reference pricing."
            )
            continue

        # A. Zero price not allowed
        if not rate:
            errors.append(f"Item {frappe.bold(item_code)}: Price cannot be zero.")
            continue

        # B. Below pricing rule floor
        rule_price = get_pricing_rule_dlits(item_code, customer, price_list,
                                            uom=uom, conversion_factor=conversion_factor)
        if rule_price is not None and round(rate, 2) < round(rule_price, 2):
            errors.append(
                f"Item {frappe.bold(item_code)}: Price ({rate}) is below "
                f"Pricing Rule ({round(rule_price, 2)})."
            )

        # C. Below last purchase rate
        if last_purchase_rate and rate < last_purchase_rate:
            errors.append(
                f"Item {frappe.bold(item_code)}: Price ({rate}) is below "
                f"Last Purchase Rate ({last_purchase_rate})."
            )

        # D. Below valuation rate
        if item_valuation_rate and rate < item_valuation_rate:
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
