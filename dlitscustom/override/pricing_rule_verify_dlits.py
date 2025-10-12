import frappe
from dlitscustom.utils.get_pricing_rule_dlits import get_pricing_rule_dlits

def pricing_rule_verify_dlits(doc, method=None):
    """Verify pricing rules compliance"""
    # Define roles that can bypass pricing rule validation
    #allowed_roles = ["", "", ""]
    allowed_roles = ["Sales Manager", "Accounts Manager", "System Manager"]
    user_roles = frappe.get_roles(frappe.session.user)
    is_allowed = any(role in allowed_roles for role in user_roles)
    if is_allowed:
        frappe.logger().info(f"User {frappe.session.user} in allowed roles, proceeding with warnings")
    
    errors = []
    items = getattr(doc, 'items', [])
    
    # Get pricing rule type from document
    pricing_rule_type = doc.get('pricing_rule_type', 'standard')
    
    for row in items:
        item_code = getattr(row, 'item_code', None)
        customer = getattr(doc, 'customer', None)
        price_list = getattr(doc, 'price_list', None) or getattr(doc, 'selling_price_list', None)
        rate = getattr(row, 'rate', None)
        valuation_rate = getattr(row, 'valuation_rate', None)
        pricing_rule_priority = row.get('priority', 1)
        
        if not item_code or rate is None:
            continue

        # Log verification details for audit trail (commented for production)
        # frappe.logger().info(f"Verified pricing rule for item {item_code} with customer {customer} and price list {price_list}")

        # Validate pricing rule implementation
        try:
            price = get_pricing_rule_dlits(item_code, customer, price_list, rate, pricing_rule_type)
            if price and row.rate != price:
                errors.append(f"Pricing rule mismatch for item {item_code}: Expected rate {price}, found {row.rate}")
                
            # Verify priority implementation
            if pricing_rule_priority != row.priority:
                errors.append(f"Priority mismatch for item {item_code}: Expected priority {pricing_rule_priority}, found {row.priority}")
                
        except Exception as e:
            frappe.log_error(f"Error verifying pricing rule for item {item_code}: {str(e)}", "Pricing Rule Verification")
        # Fetch valuation_rate and last_purchase_rate from Item master
        item_master = frappe.get_value("Item", item_code, ["valuation_rate", "last_purchase_rate"], as_dict=True) or {}
        item_valuation_rate = item_master.get("valuation_rate") or 0
        last_purchase_rate = item_master.get("last_purchase_rate") or 0
        
        # E. Check if both valuation and last purchase are 0 or null
        if (not item_valuation_rate or item_valuation_rate == 0) and (not last_purchase_rate or last_purchase_rate == 0):
            errors.append(f"Item {frappe.bold(item_code)}: Both Valuation Rate and Last Purchase Rate are zero or null. Cannot proceed without reference pricing.")
            continue
        
        # A. Not allow 0
        if rate == 0:
            errors.append(f"Item {frappe.bold(item_code)}: Price cannot be zero.")
            continue
        # B. Not allow below pricing rule
        rule_price = get_pricing_rule_dlits(item_code, customer, price_list, rate)
        # Round both values to 2 decimal places for comparison
        if rule_price is not None and round(rate, 2) < round(rule_price, 2):
            errors.append(f"Item {frappe.bold(item_code)}: Price ({rate}) is below Pricing Rule ({round(rule_price, 2)}).")
        # C. Not allow below last purchase rate
        if last_purchase_rate and rate < last_purchase_rate:
            errors.append(f"Item {frappe.bold(item_code)}: Price ({rate}) is below Last Purchase Rate ({last_purchase_rate}).")
        # D. Not allow below item master valuation rate
        if item_valuation_rate and rate < item_valuation_rate:
            errors.append(f"Item {frappe.bold(item_code)}: Price ({rate}) is below Item Valuation Rate ({item_valuation_rate}).")
        # D (alt). Not allow below doc item valuation rate
        if valuation_rate is not None and rate < valuation_rate:
            errors.append(f"Item {frappe.bold(item_code)}: Price ({rate}) is below Document Valuation Rate ({valuation_rate}).")
    if errors:
        if is_allowed:
            frappe.logger().warning(f"Pricing rule warnings for user {frappe.session.user}: {'; '.join(errors)}")
            frappe.msgprint("<br>".join(errors), title="Pricing Rule Warnings", indicator="orange")
        else:
            frappe.throw("<br>".join(errors), title="Pricing Rule Verification Failed")
