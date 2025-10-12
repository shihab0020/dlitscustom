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
        fields=["name", "discount_type", "discount_value", "priority", "apply_on", "apply_to", "base_price_type"],
    )
    if not rules:
        return None
    # Sort by: priority (asc), discount_type (Rate > Discount Percentage > Discount Amount),
    # apply_on (Item Code > Brand > Item Group), apply_to (Customer > Customer Group)
    discount_type_order = {"Rate": 0, "Discount Percentage": 1, "Discount Amount": 2}
    apply_on_order = {"Item Code": 0, "Brand": 1, "Item Group": 2}
    apply_to_order = {"Customer": 0, "Customer Group": 1}
    def rule_sort_key(rule):
        return (
            rule.get("priority", 0),
            discount_type_order.get(rule.get("discount_type"), 99),
            apply_on_order.get(rule.get("apply_on"), 99),
            apply_to_order.get(rule.get("apply_to"), 99),
        )
    rules = sorted(rules, key=rule_sort_key)
    # Try to match rules in order of priority
    for rule in rules:
        # Apply On: Item Code
        if rule.get("apply_on") == "Item Code":
            children = frappe.get_all(
                "Pricing Rule Item Code Dlits",
                filters={"parent": rule["name"], "item_code": item_code},
                fields=["item_code", "price_value"]
            )
            if children:
                # Apply To: Customer
                if rule.get("apply_to") == "Customer":
                    cust_children = frappe.get_all(
                        "Pricing Rule Customer Dlits",
                        filters={"parent": rule["name"], "customer": customer},
                        fields=["customer"]
                    )
                    if cust_children:
                        return _apply_discount(rule, item_code, price_list, children[0])
                # Apply To: Customer Group
                elif rule.get("apply_to") == "Customer Group":
                    customer_group = frappe.db.get_value("Customer", customer, "customer_group") if customer else None
                    custgrp_children = frappe.get_all(
                        "Pricing Rule Customer Group Dlits",
                        filters={"parent": rule["name"], "customer_group": customer_group},
                        fields=["customer_group"]
                    )
                    if custgrp_children:
                        return _apply_discount(rule, item_code, price_list, children[0])
        # Apply On: Brand
        elif rule.get("apply_on") == "Brand":
            brand = frappe.db.get_value("Item", item_code, "brand")
            brand_children = frappe.get_all(
                "Pricing Rule Brand Dlits",
                filters={"parent": rule["name"], "brand": brand},
                fields=["brand"]
            )
            if brand_children:
                # Apply To: Customer
                if rule.get("apply_to") == "Customer":
                    cust_children = frappe.get_all(
                        "Pricing Rule Customer Dlits",
                        filters={"parent": rule["name"], "customer": customer},
                        fields=["customer"]
                    )
                    if cust_children:
                        return _apply_discount(rule, item_code, price_list, None)
                # Apply To: Customer Group
                elif rule.get("apply_to") == "Customer Group":
                    customer_group = frappe.db.get_value("Customer", customer, "customer_group") if customer else None
                    custgrp_children = frappe.get_all(
                        "Pricing Rule Customer Group Dlits",
                        filters={"parent": rule["name"], "customer_group": customer_group},
                        fields=["customer_group"]
                    )
                    if custgrp_children:
                        return _apply_discount(rule, item_code, price_list, None)
        # Apply On: Item Group
        elif rule.get("apply_on") == "Item Group":
            item_group = frappe.db.get_value("Item", item_code, "item_group")
            group_children = frappe.get_all(
                "Pricing Rule Item Group Dlits",
                filters={"parent": rule["name"], "item_group": item_group},
                fields=["item_group"]
            )
            if group_children:
                # Apply To: Customer
                if rule.get("apply_to") == "Customer":
                    cust_children = frappe.get_all(
                        "Pricing Rule Customer Dlits",
                        filters={"parent": rule["name"], "customer": customer},
                        fields=["customer"]
                    )
                    if cust_children:
                        return _apply_discount(rule, item_code, price_list, None)
                # Apply To: Customer Group
                elif rule.get("apply_to") == "Customer Group":
                    customer_group = frappe.db.get_value("Customer", customer, "customer_group") if customer else None
                    custgrp_children = frappe.get_all(
                        "Pricing Rule Customer Group Dlits",
                        filters={"parent": rule["name"], "customer_group": customer_group},
                        fields=["customer_group"]
                    )
                    if custgrp_children:
                        return _apply_discount(rule, item_code, price_list, None)
    # No matching rule found
    return None

def _apply_discount(rule, item_code, price_list, item_row=None):
    """Apply discount/margin calculation based on rule configuration"""
    try:
        # Determine base price type
        base_price_type = rule.get("base_price_type", "Price List Rate")
        base_price = None
        
        # Production logging - single console message for pricing rule selection
        print(f"Pricing Rule Dlits applied: {rule.get('name')} for item {item_code}")
        
        # Handle Item Rate - direct price value from item table
        if base_price_type == "Item Rate":
            if item_row and item_row.get("price_value"):
                result = float(item_row.get("price_value"))
                return result
            else:
                return None
        
        # Handle other base price types
        if base_price_type == "Price List Rate":
            base_price = frappe.db.get_value(
                "Item Price",
                {"item_code": item_code, "price_list": price_list},
                "price_list_rate"
            )
        elif base_price_type == "Valuation Rate":
            base_price = frappe.db.get_value("Item", item_code, "valuation_rate")
        elif base_price_type == "Selling Rate":
            base_price = frappe.db.get_value("Item", item_code, "standard_rate")
            
            
        if base_price is None or base_price <= 0:
            return None
            
        discount_type = rule.get("discount_type", "")
        discount_value = rule.get("discount_value", 0)
        
        
        # If Valuation Rate, treat discount_value as margin (add to base)
        if base_price_type == "Valuation Rate":
            if discount_type == "Rate (Percentage)":
                # Add percentage margin to valuation rate
                result = base_price * (1 + (discount_value / 100))
            elif discount_type == "Margin Amount":
                # Add fixed margin to valuation rate
                result = base_price + discount_value
            else:
                # For other types, fallback to percentage margin
                result = base_price * (1 + (discount_value / 100))
        else:
            # For Selling Rate and Price List Rate, treat as discount
            if discount_type == "Rate (Percentage)":
                # Return calculated price with percentage discount
                result = base_price * (1 - (discount_value / 100))
            elif discount_type == "Discount Percentage":
                result = base_price * (1 - (discount_value / 100))
            elif discount_type == "Discount Amount":
                result = max(0, base_price - discount_value)  # Ensure non-negative
            else:
                result = base_price
                
        return result
        
    except Exception as e:
        frappe.log_error(f"Error in _apply_discount: {str(e)}", "Pricing Rule Calculation")
        return None
