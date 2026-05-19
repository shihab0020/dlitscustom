import frappe


@frappe.whitelist()
def get_pricing_rule_dlits(item_code, customer=None, price_list=None, base_price=None,
                           uom=None, conversion_factor=1.0):
    """
    Return the minimum allowed price for item_code under the matching Pricing Rule Dlits.
    conversion_factor: how many stock UOM units equal one transaction UOM unit (from the doc row).
    All base prices (valuation rate, price list rate) are stored in stock UOM and are multiplied
    by conversion_factor before discount/margin is applied.
    """
    conversion_factor = float(conversion_factor or 1.0)

    rules = frappe.get_all(
        "Pricing Rule Dlits",
        filters={"enabled": 1, "price_list": price_list},
        fields=["name", "discount_type", "discount_value", "priority",
                "apply_on", "apply_to", "base_price_type"],
    )
    if not rules:
        return None

    rules = sorted(rules, key=lambda r: (
        r.get("priority", 0),
        {"Rate": 0, "Discount Percentage": 1, "Discount Amount": 2}.get(r.get("discount_type"), 99),
        {"Item Code": 0, "Brand": 1, "Item Group": 2}.get(r.get("apply_on"), 99),
        {"Customer": 0, "Customer Group": 1}.get(r.get("apply_to"), 99),
    ))

    for rule in rules:
        item_row = _match_apply_on(rule, item_code)
        if item_row is None:
            continue
        if not _match_apply_to(rule, customer):
            continue
        return _apply_discount(rule, item_code, price_list, item_row, uom, conversion_factor)

    return None


# ── matching helpers ──────────────────────────────────────────────────────────

def _match_apply_on(rule, item_code):
    """
    Return the matched child row (or True for non-item-code rules) if the rule
    applies to this item, else None.
    """
    apply_on = rule.get("apply_on")

    if apply_on == "Item Code":
        rows = frappe.get_all(
            "Pricing Rule Item Code Dlits",
            filters={"parent": rule["name"], "item_code": item_code},
            fields=["item_code", "price_value"],
        )
        return rows[0] if rows else None

    if apply_on == "Brand":
        brand = frappe.db.get_value("Item", item_code, "brand")
        if brand and frappe.get_all("Pricing Rule Brand Dlits",
                                    filters={"parent": rule["name"], "brand": brand}):
            return True
        return None

    if apply_on == "Item Group":
        item_group = frappe.db.get_value("Item", item_code, "item_group")
        if item_group and frappe.get_all("Pricing Rule Item Group Dlits",
                                         filters={"parent": rule["name"], "item_group": item_group}):
            return True
        return None

    return None


def _match_apply_to(rule, customer):
    apply_to = rule.get("apply_to")

    if apply_to == "Customer":
        return bool(frappe.get_all(
            "Pricing Rule Customer Dlits",
            filters={"parent": rule["name"], "customer": customer},
        ))

    if apply_to == "Customer Group":
        customer_group = frappe.db.get_value("Customer", customer, "customer_group") if customer else None
        return bool(frappe.get_all(
            "Pricing Rule Customer Group Dlits",
            filters={"parent": rule["name"], "customer_group": customer_group},
        ))

    return False


# ── price calculation ─────────────────────────────────────────────────────────

def _apply_discount(rule, item_code, price_list, item_row=None, uom=None, conversion_factor=1.0):
    base_price_type = rule.get("base_price_type", "Price List Rate")

    if base_price_type == "Item Rate":
        if item_row and item_row.get("price_value"):
            # price_value is stored per stock UOM
            return float(item_row["price_value"]) * conversion_factor
        return None

    base_price = _get_base_price(base_price_type, item_code, price_list, uom, conversion_factor)
    if not base_price or base_price <= 0:
        return None

    discount_type = rule.get("discount_type", "")
    discount_value = float(rule.get("discount_value") or 0)

    if base_price_type == "Valuation Rate":
        # Valuation rate rules use margin (add to cost)
        if discount_type == "Rate (Percentage)":
            return base_price * (1 + discount_value / 100)
        if discount_type == "Margin Amount":
            return base_price + discount_value
        return base_price * (1 + discount_value / 100)
    else:
        # Price list / selling rate rules use discount (subtract from price)
        if discount_type in ("Rate (Percentage)", "Discount Percentage"):
            return base_price * (1 - discount_value / 100)
        if discount_type == "Discount Amount":
            return max(0.0, base_price - discount_value)
        return base_price


def _get_base_price(base_price_type, item_code, price_list, uom, conversion_factor):
    """
    Fetch the base price in stock UOM and scale to the transaction UOM.
    For Price List Rate we first try to find a price entry matching the transaction UOM;
    if none exists we fall back to the stock-UOM price and multiply by conversion_factor.
    """
    if base_price_type == "Price List Rate":
        # 1. Try exact UOM match in Item Price
        if uom:
            price = frappe.db.get_value(
                "Item Price",
                {"item_code": item_code, "price_list": price_list, "uom": uom},
                "price_list_rate",
            )
            if price:
                return float(price)
        # 2. Fall back to any price for this price list (stock UOM) and convert
        price = frappe.db.get_value(
            "Item Price",
            {"item_code": item_code, "price_list": price_list},
            "price_list_rate",
        )
        return float(price) * conversion_factor if price else None

    if base_price_type == "Valuation Rate":
        rate = frappe.db.get_value("Item", item_code, "valuation_rate") or 0
        return float(rate) * conversion_factor

    if base_price_type == "Selling Rate":
        rate = frappe.db.get_value("Item", item_code, "standard_rate") or 0
        return float(rate) * conversion_factor

    return None
