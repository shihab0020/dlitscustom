import frappe
from dlitscustom.utils.get_pricing_rule_dlits import get_pricing_rule_dlits

@frappe.whitelist()
def test_item_rate_calculation():
    """Test Item Rate pricing rule calculation"""
    
    try:
        print("=== TESTING ITEM RATE PRICING RULE ===")
        
        # Test the Item Rate pricing rule we just created
        result = get_pricing_rule_dlits('item10', 'Customer10', 'Standard Selling')
        
        print(f"Item Rate pricing rule result: {result}")
        print(f"Expected: 120.0 (direct price value from item table)")
        
        if result == 120.0:
            print("✅ SUCCESS: Item Rate pricing rule working correctly!")
            return {
                "success": True,
                "result": result,
                "expected": 120.0,
                "message": "Item Rate pricing rule working correctly"
            }
        else:
            print(f"❌ ERROR: Expected 120.0, got {result}")
            return {
                "success": False,
                "result": result,
                "expected": 120.0,
                "message": f"Expected 120.0, got {result}"
            }
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }