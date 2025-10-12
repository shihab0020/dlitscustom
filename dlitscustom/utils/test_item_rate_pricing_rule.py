import frappe

@frappe.whitelist()
def test_create_item_rate_pricing_rule():
    """Test creating a pricing rule with Item Rate base price type"""
    
    try:
        # Create a new pricing rule with Item Rate
        doc = frappe.new_doc("Pricing Rule Dlits")
        doc.name = "Test-Item-Rate-Rule"
        doc.enabled = 1
        doc.priority = 1
        doc.price_list = "Standard Selling"
        doc.base_price_type = "Item Rate"
        # Note: discount_type and discount_value should not be required
        doc.apply_on = "Item Code"
        doc.apply_to = "Customer"
        
        # Add an item with price value
        doc.append("items", {
            "item_code": "item10",
            "price_value": 120.0
        })
        
        # Add a customer
        doc.append("customers", {
            "customer": "Customer10"
        })
        
        # Try to save
        doc.insert()
        
        print(f"SUCCESS: Created pricing rule '{doc.name}' with Item Rate base price type")
        print(f"  Base Price Type: {doc.base_price_type}")
        print(f"  Discount Type: {doc.discount_type}")
        print(f"  Discount Value: {doc.discount_value}")
        print(f"  Item Price Value: {doc.items[0].price_value}")
        
        return {
            "success": True,
            "message": "Pricing rule created successfully",
            "name": doc.name,
            "base_price_type": doc.base_price_type,
            "discount_type": doc.discount_type,
            "discount_value": doc.discount_value
        }
        
    except Exception as e:
        print(f"ERROR: Failed to create pricing rule: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }