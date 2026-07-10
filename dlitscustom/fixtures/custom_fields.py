import frappe


def create_all_custom_fields():
    """Create all custom fields for the app."""
    try:
        print("   Creating all custom fields...")
        create_sales_invoice_commission_fields()
        create_sales_invoice_invoice_commission_fields()
        create_quotation_margin_fields()
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


def create_sales_invoice_invoice_commission_fields():
    """Add Buyer Representative / Fixed Commission fields to Sales Invoice."""
    fields = [
        {
            "doctype": "Custom Field",
            "dt": "Sales Invoice",
            "fieldname": "dlits_buyer_rep_section",
            "label": "Buyer Representative Commission",
            "fieldtype": "Tab Break",
            "insert_after": "custom_private_note",
        },
        {
            "doctype": "Custom Field",
            "dt": "Sales Invoice",
            "fieldname": "dlits_buyer_representative",
            "label": "Buyer Representative",
            "fieldtype": "Link",
            "options": "Dlits Sales Partner",
            "insert_after": "dlits_buyer_rep_section",
            "allow_on_submit": 0,
            "description": "External agent / buyer rep who arranged this deal (fixed commission)",
        },
        {
            "doctype": "Custom Field",
            "dt": "Sales Invoice",
            "fieldname": "dlits_fixed_commission",
            "label": "Fixed Commission",
            "fieldtype": "Currency",
            "insert_after": "dlits_buyer_representative",
            "allow_on_submit": 0,
            "description": "Agreed lump-sum commission for the buyer representative",
        },
        {
            "doctype": "Custom Field",
            "dt": "Sales Invoice",
            "fieldname": "dlits_commission_ref",
            "label": "Commission Record",
            "fieldtype": "Link",
            "options": "Dlits Invoice Commission",
            "insert_after": "dlits_fixed_commission",
            "allow_on_submit": 1,
            "read_only": 1,
            "print_hide": 1,
            "description": "Auto-linked when invoice is submitted",
        },
    ]

    for field_data in fields:
        if not frappe.db.exists("Custom Field", {"dt": field_data["dt"], "fieldname": field_data["fieldname"]}):
            doc = frappe.get_doc(field_data)
            doc.insert(ignore_permissions=True)
            print(f"   Created: {field_data['fieldname']} on {field_data['dt']}")
        else:
            print(f"   Already exists: {field_data['fieldname']} on {field_data['dt']}")

    frappe.db.commit()


def create_quotation_margin_fields():
    """Add Dlits Margin Table section to Quotation, Sales Order, Sales Invoice."""
    _create_margin_fields_for("Quotation",     "last_scanned_warehouse")
    _create_margin_fields_for("Sales Order",   "last_scanned_warehouse")
    _create_margin_fields_for("Sales Invoice", "last_scanned_warehouse")


def _create_margin_fields_for(dt, insert_after):
    fields = [
        {"doctype": "Custom Field", "dt": dt, "fieldname": "dlits_margin_section",
         "label": "Dlits Margin Analysis", "fieldtype": "Section Break",
         "insert_after": insert_after, "collapsible": 1},
        {"doctype": "Custom Field", "dt": dt, "fieldname": "dlits_margin_table",
         "label": "", "fieldtype": "Table", "options": "Dlits Margin Table Item",
         "insert_after": "dlits_margin_section"},
        {"doctype": "Custom Field", "dt": dt, "fieldname": "dlits_margin_summary",
         "label": "", "fieldtype": "HTML", "insert_after": "dlits_margin_table"},
        {"doctype": "Custom Field", "dt": dt, "fieldname": "dlits_margin_end_sb",
         "label": "", "fieldtype": "Section Break", "insert_after": "dlits_margin_summary"},
    ]
    for field_data in fields:
        fn = field_data["fieldname"]
        if not frappe.db.exists("Custom Field", {"dt": dt, "fieldname": fn}):
            frappe.get_doc(field_data).insert(ignore_permissions=True)
            print(f"   Created: {fn} on {dt}")
        else:
            print(f"   Already exists: {fn} on {dt}")
    frappe.db.commit()


def remove_custom_fields():
    """Remove all custom fields created by the app (used during uninstall)."""
    try:
        print("   Removing custom fields...")

        fields_to_remove = [
            # Sales Invoice commission fields
            {"dt": "Sales Invoice", "fieldname": "dlits_sales_partner"},
            {"dt": "Sales Invoice", "fieldname": "dlits_is_me"},
            # Sales Invoice invoice commission fields
            {"dt": "Sales Invoice", "fieldname": "dlits_buyer_rep_section"},
            {"dt": "Sales Invoice", "fieldname": "dlits_buyer_representative"},
            {"dt": "Sales Invoice", "fieldname": "dlits_fixed_commission"},
            {"dt": "Sales Invoice", "fieldname": "dlits_commission_ref"},
            # Margin fields (Quotation, Sales Order, Sales Invoice)
            {"dt": "Quotation",     "fieldname": "dlits_margin_section"},
            {"dt": "Quotation",     "fieldname": "dlits_margin_table"},
            {"dt": "Quotation",     "fieldname": "dlits_margin_summary"},
            {"dt": "Quotation",     "fieldname": "dlits_margin_end_sb"},
            {"dt": "Sales Order",   "fieldname": "dlits_margin_section"},
            {"dt": "Sales Order",   "fieldname": "dlits_margin_table"},
            {"dt": "Sales Order",   "fieldname": "dlits_margin_summary"},
            {"dt": "Sales Order",   "fieldname": "dlits_margin_end_sb"},
            {"dt": "Sales Invoice", "fieldname": "dlits_margin_section"},
            {"dt": "Sales Invoice", "fieldname": "dlits_margin_table"},
            {"dt": "Sales Invoice", "fieldname": "dlits_margin_summary"},
            {"dt": "Sales Invoice", "fieldname": "dlits_margin_end_sb"},
            # Legacy column-break totals fields (removed in v2 layout)
            {"dt": "Quotation", "fieldname": "dlits_total_selling"},
            {"dt": "Quotation", "fieldname": "dlits_total_cost_amount"},
            {"dt": "Quotation", "fieldname": "dlits_margin_cb1"},
            {"dt": "Quotation", "fieldname": "dlits_gross_margin"},
            {"dt": "Quotation", "fieldname": "dlits_gross_margin_pct"},
            {"dt": "Quotation", "fieldname": "dlits_margin_cb2"},
            {"dt": "Quotation", "fieldname": "dlits_net_margin"},
            {"dt": "Quotation", "fieldname": "dlits_net_margin_pct"},
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
