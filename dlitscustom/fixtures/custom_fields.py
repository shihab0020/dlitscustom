import frappe


def create_all_custom_fields():
    """Create all custom fields for the app."""
    try:
        print("   Creating all custom fields...")
        create_sales_invoice_commission_fields()
        print("   All custom fields created successfully")
    except Exception as e:
        print(f"   Error creating all custom fields: {str(e)}")
        raise


def create_sales_invoice_commission_fields():
    """Add Dlits Sales Partner fields to Sales Invoice."""
    fields = [
        {
            "doctype": "Custom Field",
            "dt": "Sales Invoice",
            "fieldname": "dlits_sales_partner",
            "label": "Dlits Sales Partner",
            "fieldtype": "Link",
            "options": "Dlits Sales Partner",
            "insert_after": "set_posting_time",
            "allow_on_submit": 1,
            "description": "Select Dlits Sales Partner for commission tracking"
        },
        {
            "doctype": "Custom Field",
            "dt": "Sales Invoice",
            "fieldname": "dlits_is_me",
            "label": "Me",
            "fieldtype": "Check",
            "insert_after": "dlits_sales_partner",
            "allow_on_submit": 1,
            "description": "Tick to auto-fill your linked Sales Partner"
        }
    ]

    for field_data in fields:
        if not frappe.db.exists("Custom Field", {"dt": field_data["dt"], "fieldname": field_data["fieldname"]}):
            doc = frappe.get_doc(field_data)
            doc.insert(ignore_permissions=True)
            print(f"   Created: {field_data['fieldname']} on {field_data['dt']}")
        else:
            print(f"   Already exists: {field_data['fieldname']} on {field_data['dt']}")

    frappe.db.commit()


def remove_custom_fields():
    """Remove all custom fields created by the app (used during uninstall)."""
    try:
        print("   Removing custom fields...")

        fields_to_remove = [
            # Sales Invoice commission fields
            {"dt": "Sales Invoice", "fieldname": "dlits_sales_partner"},
            {"dt": "Sales Invoice", "fieldname": "dlits_is_me"},
            # Legacy fields (cleanup safety net)
            {"dt": "Sales Invoice", "fieldname": "dlits_commission_section"},
            {"dt": "Sales Invoice", "fieldname": "dlits_commission_type"},
            {"dt": "Sales Invoice", "fieldname": "dlits_commission_rate"},
            {"dt": "Sales Invoice", "fieldname": "column_break_commission"},
            {"dt": "Sales Invoice", "fieldname": "dlits_commission_amount"},
            {"dt": "Sales Invoice", "fieldname": "dlits_commission_paid_amount"},
            {"dt": "Sales Invoice", "fieldname": "dlits_commission_outstanding"},
            {"dt": "Sales Order", "fieldname": "dlits_commission_section"},
            {"dt": "Sales Order", "fieldname": "dlits_sales_partner"},
            {"dt": "Sales Order", "fieldname": "dlits_commission_type"},
            {"dt": "Sales Order", "fieldname": "dlits_commission_rate"},
            {"dt": "Sales Order", "fieldname": "column_break_commission"},
            {"dt": "Sales Order", "fieldname": "dlits_commission_amount"},
        ]

        for field_info in fields_to_remove:
            cf_name = frappe.db.get_value(
                "Custom Field",
                {"dt": field_info["dt"], "fieldname": field_info["fieldname"]},
                "name"
            )
            if cf_name:
                frappe.delete_doc("Custom Field", cf_name, ignore_permissions=True)
                print(f"   Removed: {field_info['fieldname']} from {field_info['dt']}")

        frappe.db.commit()
        print("   Custom fields removed successfully")

    except Exception as e:
        print(f"   Error removing custom fields: {str(e)}")
        raise
