#!/usr/bin/env python3

import frappe

def update_custom_fields():
    """Update existing custom fields to allow editing after submit"""
    
    # Connect to the site
    frappe.init(site='dlitsdev1')
    frappe.connect()
    
    # Fields to update with allow_on_submit = 1
    fields_to_update = [
        {"dt": "Sales Invoice", "fieldname": "dlits_sales_partner"},
        {"dt": "Sales Invoice", "fieldname": "dlits_commission_type"},
        {"dt": "Sales Invoice", "fieldname": "dlits_commission_amount"}
    ]
    
    for field_info in fields_to_update:
        try:
            # Get the custom field
            custom_field_name = frappe.db.get_value(
                "Custom Field", 
                {"dt": field_info["dt"], "fieldname": field_info["fieldname"]}, 
                "name"
            )
            
            if custom_field_name:
                # Update the custom field
                custom_field = frappe.get_doc("Custom Field", custom_field_name)
                custom_field.allow_on_submit = 1
                custom_field.read_only = 0  # Remove read_only restriction
                custom_field.save()
                print(f"Updated {field_info['fieldname']} for {field_info['dt']}")
            else:
                print(f"Custom field not found: {field_info['fieldname']} for {field_info['dt']}")
                
        except Exception as e:
            print(f"Error updating {field_info['fieldname']}: {str(e)}")
    
    # Commit changes
    frappe.db.commit()
    print("All custom fields updated successfully")

if __name__ == "__main__":
    update_custom_fields()