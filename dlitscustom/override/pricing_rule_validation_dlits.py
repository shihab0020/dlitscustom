import frappe
from dlitscustom.utils.get_pricing_rule_dlits import get_pricing_rule_dlits

def pricing_rule_validation_dlits(doc, method=None):
    """Apply custom pricing rules to document items"""
    # Validate required fields
    required_fields = ['items', 'customer', 'price_list', 'selling_price_list']
    for field in required_fields:
        if not getattr(doc, field, None):
            frappe.throw(f"Missing required field: {field}")
    
    # Loop through items for Sales Invoice, Sales Order, Quotation
    items = getattr(doc, 'items', [])
    for row in items:
        item_code = getattr(row, 'item_code', None)
        customer = getattr(doc, 'customer', None)
        price_list = getattr(doc, 'price_list', None) or getattr(doc, 'selling_price_list', None)
        base_price = getattr(row, 'price_list_rate', None) or getattr(row, 'rate', None)
        
        if not item_code or not price_list or not base_price:
            continue
            
        try:
            # Get pricing rule type from document
            pricing_rule_type = doc.get('pricing_rule_type', 'standard')
            price = get_pricing_rule_dlits(item_code, customer, price_list, base_price, pricing_rule_type)
            
            if price:
                # Set both rate and price_list_rate for compatibility
                if hasattr(row, 'rate'):
                    row.rate = price
                if hasattr(row, 'price_list_rate'):
                    row.price_list_rate = price
                    
                # Set priority for pricing rules
                row.priority = doc.get('pricing_rule_priority', 1)
        except Exception as e:
            frappe.log_error(f"Error applying pricing rule: {str(e)}", "Pricing Rule Validation")
