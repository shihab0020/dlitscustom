import frappe

def create_commission_fields():
    """Create commission custom fields manually"""
    try:
        print("Creating commission custom fields...")
        
        # Import the function
        from dlitscustom.fixtures.custom_fields import create_commission_custom_fields
        
        # Create the fields
        create_commission_custom_fields()
        
        # Commit to database
        frappe.db.commit()
        
        print("Commission custom fields created successfully!")
        print("Please refresh your Sales Invoice and Sales Order forms to see the new fields.")
        
        return True
        
    except Exception as e:
        print(f"Error creating commission fields: {str(e)}")
        frappe.log_error(f"Error creating commission fields: {str(e)}")
        return False

if __name__ == "__main__":
    create_commission_fields()