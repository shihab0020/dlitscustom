import frappe
import json

def create_sales_partner_custom_fields():
    """Legacy function - ERPNext Sales Partner fields no longer needed"""
    try:
        print("   Skipping legacy ERPNext Sales Partner custom fields (using DLITS Sales Partner instead)")
        return True
        
    except Exception as e:
        print(f"   Error in legacy function: {str(e)}")
        raise

def create_commission_custom_fields():
    """Create commission-related custom fields for Sales Invoice and Sales Order"""
    try:
        print("   Creating commission custom fields...")
        
        # Commission fields for Sales Invoice
        sales_invoice_fields = [
            {
                "doctype": "Custom Field",
                "dt": "Sales Invoice",
                "fieldname": "dlits_commission_section",
                "label": "DLITS Commission",
                "fieldtype": "Section Break",
                "insert_after": "sales_partner",
                "collapsible": 1
            },
            {
                "doctype": "Custom Field",
                "dt": "Sales Invoice",
                "fieldname": "dlits_sales_partner",
                "label": "DLITS Sales Partner",
                "fieldtype": "Link",
                "options": "DLITS Sales Partner",
                "insert_after": "dlits_commission_section",
                "description": "Select DLITS Sales Partner for commission calculation",
                "allow_on_submit": 1
            },
            {
                "doctype": "Custom Field",
                "dt": "Sales Invoice",
                "fieldname": "dlits_commission_type",
                "label": "Commission Type",
                "fieldtype": "Select",
                "options": "Percentage\nFixed Amount",
                "insert_after": "dlits_sales_partner",
                "allow_on_submit": 1
            },
            {
                "doctype": "Custom Field",
                "dt": "Sales Invoice",
                "fieldname": "dlits_commission_rate",
                "label": "Commission Rate",
                "fieldtype": "Float",
                "precision": "2",
                "insert_after": "dlits_commission_type",
                "read_only": 1
            },
            {
                "doctype": "Custom Field",
                "dt": "Sales Invoice",
                "fieldname": "column_break_commission",
                "fieldtype": "Column Break",
                "insert_after": "dlits_commission_rate"
            },
            {
                "doctype": "Custom Field",
                "dt": "Sales Invoice",
                "fieldname": "dlits_commission_amount",
                "label": "Commission Amount",
                "fieldtype": "Currency",
                "insert_after": "column_break_commission",
                "allow_on_submit": 1
            },
            {
                "doctype": "Custom Field",
                "dt": "Sales Invoice",
                "fieldname": "dlits_commission_paid_amount",
                "label": "Commission Paid Amount",
                "fieldtype": "Currency",
                "insert_after": "dlits_commission_amount",
                "default": "0",
                "description": "Amount of commission already paid"
            },
            {
                "doctype": "Custom Field",
                "dt": "Sales Invoice",
                "fieldname": "dlits_commission_outstanding",
                "label": "Outstanding Commission",
                "fieldtype": "Currency",
                "insert_after": "dlits_commission_paid_amount",
                "read_only": 1
            }
        ]
        
        # Commission fields for Sales Order
        sales_order_fields = [
            {
                "doctype": "Custom Field",
                "dt": "Sales Order",
                "fieldname": "dlits_commission_section",
                "label": "DLITS Commission",
                "fieldtype": "Section Break",
                "insert_after": "sales_partner",
                "collapsible": 1
            },
            {
                "doctype": "Custom Field",
                "dt": "Sales Order",
                "fieldname": "dlits_sales_partner",
                "label": "DLITS Sales Partner",
                "fieldtype": "Link",
                "options": "DLITS Sales Partner",
                "insert_after": "dlits_commission_section",
                "description": "Select DLITS Sales Partner for commission calculation"
            },
            {
                "doctype": "Custom Field",
                "dt": "Sales Order",
                "fieldname": "dlits_commission_type",
                "label": "Commission Type",
                "fieldtype": "Select",
                "options": "Percentage\nFixed Amount",
                "insert_after": "dlits_sales_partner",
                "read_only": 1
            },
            {
                "doctype": "Custom Field",
                "dt": "Sales Order",
                "fieldname": "dlits_commission_rate",
                "label": "Commission Rate",
                "fieldtype": "Float",
                "precision": "2",
                "insert_after": "dlits_commission_type",
                "read_only": 1
            },
            {
                "doctype": "Custom Field",
                "dt": "Sales Order",
                "fieldname": "column_break_commission",
                "fieldtype": "Column Break",
                "insert_after": "dlits_commission_rate"
            },
            {
                "doctype": "Custom Field",
                "dt": "Sales Order",
                "fieldname": "dlits_commission_amount",
                "label": "Commission Amount",
                "fieldtype": "Currency",
                "insert_after": "column_break_commission",
                "read_only": 1
            }
        ]
        
        # Create all custom fields
        all_fields = sales_invoice_fields + sales_order_fields
        
        for field_data in all_fields:
            if not frappe.db.exists("Custom Field", {"dt": field_data["dt"], "fieldname": field_data["fieldname"]}):
                custom_field = frappe.get_doc(field_data)
                custom_field.insert(ignore_permissions=True)
                print(f"   Created custom field: {field_data['fieldname']} for {field_data['dt']}")
            else:
                print(f"   Custom field already exists: {field_data['fieldname']} for {field_data['dt']}")
        
        frappe.db.commit()
        print("   Commission custom fields created successfully")
        
    except Exception as e:
        print(f"   Error creating commission custom fields: {str(e)}")
        raise

def remove_custom_fields():
    """Remove custom fields created by the app"""
    try:
        print("   Removing custom fields...")
        
        # List of custom fields to remove
        fields_to_remove = [
            # Legacy Sales Partner fields (clean up old references)
            {"dt": "Sales Partner", "fieldname": "supplier"},
            {"dt": "Sales Partner", "fieldname": "auto_create_supplier"},
            
            # Sales Invoice commission fields
            {"dt": "Sales Invoice", "fieldname": "dlits_commission_section"},
            {"dt": "Sales Invoice", "fieldname": "dlits_sales_partner"},
            {"dt": "Sales Invoice", "fieldname": "dlits_commission_type"},
            {"dt": "Sales Invoice", "fieldname": "dlits_commission_rate"},
            {"dt": "Sales Invoice", "fieldname": "column_break_commission"},
            {"dt": "Sales Invoice", "fieldname": "dlits_commission_amount"},
            {"dt": "Sales Invoice", "fieldname": "dlits_commission_paid_amount"},
            {"dt": "Sales Invoice", "fieldname": "dlits_commission_outstanding"},
            
            # Sales Order commission fields
            {"dt": "Sales Order", "fieldname": "dlits_commission_section"},
            {"dt": "Sales Order", "fieldname": "dlits_sales_partner"},
            {"dt": "Sales Order", "fieldname": "dlits_commission_type"},
            {"dt": "Sales Order", "fieldname": "dlits_commission_rate"},
            {"dt": "Sales Order", "fieldname": "column_break_commission"},
            {"dt": "Sales Order", "fieldname": "dlits_commission_amount"}
        ]
        
        for field_info in fields_to_remove:
            if frappe.db.exists("Custom Field", {"dt": field_info["dt"], "fieldname": field_info["fieldname"]}):
                frappe.delete_doc("Custom Field",
                    frappe.db.get_value("Custom Field",
                        {"dt": field_info["dt"], "fieldname": field_info["fieldname"]}, "name"),
                    ignore_permissions=True)
                print(f"   Removed custom field: {field_info['fieldname']} from {field_info['dt']}")
            else:
                print(f"   Custom field not found: {field_info['fieldname']} in {field_info['dt']}")
        
        frappe.db.commit()
        print("   Custom fields removed successfully")
        
    except Exception as e:
        print(f"   Error removing custom fields: {str(e)}")
        raise

def create_all_custom_fields():
    """Create all custom fields for the app"""
    try:
        print("   Creating all custom fields...")
        
        # Skip legacy sales partner fields (using DLITS Sales Partner instead)
        print("   Skipping legacy ERPNext Sales Partner fields")
        
        # Create commission fields
        create_commission_custom_fields()
        
        print("   All custom fields created successfully")
        
    except Exception as e:
        print(f"   Error creating all custom fields: {str(e)}")
        raise

def create_item_custom_fields():
    """Create custom fields for Item if needed"""
    try:
        # Add any item-specific custom fields here if needed in the future
        pass
    except Exception as e:
        print(f"   Error creating item custom fields: {str(e)}")
        raise

def create_sales_order_custom_fields():
    """Create custom fields for Sales Order if needed"""
    try:
        # Add any sales order-specific custom fields here if needed in the future
        pass
    except Exception as e:
        print(f"   Error creating sales order custom fields: {str(e)}")
        raise