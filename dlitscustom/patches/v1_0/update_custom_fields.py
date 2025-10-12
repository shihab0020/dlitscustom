import frappe
from frappe import _

def execute():
    """
    Migration patch to ensure custom fields are properly created/updated
    """
    try:
        print("Running custom fields migration patch...")
        
        # Import and run custom field creation
        from dlitscustom.fixtures.custom_fields import create_sales_partner_custom_fields
        create_sales_partner_custom_fields()
        
        # Clear cache to ensure changes are reflected
        frappe.clear_cache()
        
        print("Custom fields migration patch completed successfully!")
        
    except Exception as e:
        print(f"Error in custom fields migration patch: {str(e)}")
        frappe.log_error(f"Custom fields migration patch error: {str(e)}")
        raise