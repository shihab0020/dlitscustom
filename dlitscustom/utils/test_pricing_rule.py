import frappe
from dlitscustom.utils.get_pricing_rule_dlits import get_pricing_rule_dlits

@frappe.whitelist()
def test_pricing_rule_debug():
    """Test function to debug pricing rule calculation"""
    
    # Test with your specific case
    item_code = "item10"
    customer = "customer10"
    price_list = "Standard Selling"
    
    print(f"\n=== DEBUGGING PRICING RULE ===")
    print(f"Item: {item_code}")
    print(f"Customer: {customer}")
    print(f"Price List: {price_list}")
    
    # Check if item exists and get its standard_rate
    item_data = frappe.db.get_value("Item", item_code, ["standard_rate", "valuation_rate"], as_dict=True)
    if item_data:
        print(f"Item standard_rate: {item_data.get('standard_rate')}")
        print(f"Item valuation_rate: {item_data.get('valuation_rate')}")
    else:
        print(f"Item {item_code} not found!")
        return
    
    # Check if customer exists
    customer_exists = frappe.db.exists("Customer", customer)
    print(f"Customer exists: {customer_exists}")
    
    # Check if price list exists
    price_list_exists = frappe.db.exists("Price List", price_list)
    print(f"Price List exists: {price_list_exists}")
    
    # Find pricing rules for this price list
    rules = frappe.get_all(
        "Pricing Rule Dlits",
        filters={
            "enabled": 1,
            "price_list": price_list,
        },
        fields=["name", "discount_type", "discount_value", "priority", "apply_on", "apply_to", "base_price_type"],
    )
    
    print(f"\nFound {len(rules)} pricing rules:")
    for rule in rules:
        print(f"  Rule: {rule['name']}")
        print(f"    Base Price Type: {rule['base_price_type']}")
        print(f"    Discount Type: {rule['discount_type']}")
        print(f"    Discount Value: {rule['discount_value']}")
        print(f"    Apply On: {rule['apply_on']}")
        print(f"    Apply To: {rule['apply_to']}")
        
        # Check if this rule applies to our item
        if rule['apply_on'] == 'Item Code':
            items = frappe.get_all(
                "Pricing Rule Item Code Dlits",
                filters={"parent": rule["name"], "item_code": item_code},
                fields=["item_code", "price_value"]
            )
            print(f"    Item matches: {len(items) > 0}")
            if items:
                print(f"    Price Value: {items[0].get('price_value')}")
        
        # Check if this rule applies to our customer
        if rule['apply_to'] == 'Customer':
            customers = frappe.get_all(
                "Pricing Rule Customer Dlits",
                filters={"parent": rule["name"], "customer": customer},
                fields=["customer"]
            )
            print(f"    Customer matches: {len(customers) > 0}")
    
    # Test the actual pricing function
    print(f"\n=== TESTING PRICING FUNCTION ===")
    result = get_pricing_rule_dlits(item_code, customer, price_list)
    print(f"Pricing rule result: {result}")
    
    if result:
        expected = item_data.get('standard_rate', 0) * (1 - 25/100)  # 25% discount
        print(f"Expected result (140 * 0.75): {expected}")
        print(f"Difference: {result - expected}")
    
    return {
        "item_data": item_data,
        "rules_found": len(rules),
        "pricing_result": result,
        "expected": item_data.get('standard_rate', 0) * 0.75 if item_data else None
    }