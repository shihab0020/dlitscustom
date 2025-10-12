import frappe

@frappe.whitelist()
def update_test_pricing_rule():
    """Update Test0 pricing rule to use percentage discount"""
    
    try:
        doc = frappe.get_doc('Pricing Rule Dlits', 'Test0')
        
        print(f"Before update:")
        print(f"  Discount Type: {doc.discount_type}")
        print(f"  Discount Value: {doc.discount_value}")
        
        # Update to correct configuration
        doc.base_price_type = 'Selling Rate'
        doc.discount_type = 'Discount Percentage'
        doc.discount_value = 25.0
        doc.save()
        
        print(f"After update:")
        print(f"  Base Price Type: {doc.base_price_type}")
        print(f"  Discount Type: {doc.discount_type}")
        print(f"  Discount Value: {doc.discount_value}")
        
        return {
            "success": True,
            "message": "Pricing rule updated successfully",
            "base_price_type": doc.base_price_type,
            "discount_type": doc.discount_type,
            "discount_value": doc.discount_value
        }
        
    except Exception as e:
        print(f"Error updating pricing rule: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }