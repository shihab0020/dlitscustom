import frappe

@frappe.whitelist()
def get_pricing_rule_dlits(item_code, customer=None, price_list=None, base_price=None):
    # Find enabled Pricing Rule Dlits for this price list
    rules = frappe.get_all(
        "Pricing Rule Dlits",
        filters={
            "enabled": 1,
            "price_list": price_list,
        },
        fields=["name", "discount_type", "discount_value", "priority"]
    )
    if not rules:
        return None
    # Sort by priority (lower number = higher priority)
    rules = sorted(rules, key=lambda x: x.get("priority", 0))
    # Try to match item_code in child table if possible
    for rule in rules:
        children = frappe.get_all(
            "Pricing Rule Item Code Dlits",
            filters={"parent": rule["name"], "item_code": item_code},
            fields=["item_code"]
        )
        if children:
            # Found a rule for this item_code
            return _apply_discount(rule, item_code, price_list)
    # If no child match, fallback to first rule
    rule = rules[0]
    return _apply_discount(rule, item_code, price_list)

def _apply_discount(rule, item_code, price_list):
    # Always fetch the original price from Item Price table
    base_price = frappe.db.get_value(
        "Item Price",
        {"item_code": item_code, "price_list": price_list},
        "price_list_rate"
    )
    if base_price is None:
        return None
    if rule["discount_type"] == "Rate":
        return rule["discount_value"]
    elif rule["discount_type"] == "Discount Percentage":
        return base_price * (1 - (rule["discount_value"] / 100))
    elif rule["discount_type"] == "Discount Amount":
        return base_price - rule["discount_value"]
    return None
