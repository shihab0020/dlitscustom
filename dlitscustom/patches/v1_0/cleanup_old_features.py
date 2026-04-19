import frappe


def execute():
    """
    Remove all old DLITS features: doctype tables, custom fields, and report records.
    Covers: DLITS Sales Partner, Employee Tools Allocation, Tools Transfer Dlits,
    and all their associated reports and custom fields.
    """

    # --- 1. Drop old doctype database tables ---
    tables_to_drop = [
        # DLITS Sales Partner and its child tables
        "tabDLITS Sales Partner",
        "tabDLITS Sales Partner Commission Entry",
        # Employee Tools Allocation and its child tables
        "tabEmployee Tools Allocation",
        "tabEmployee Tools Allocation Item",
        # Tools Transfer Dlits and its child tables
        "tabTools Transfer Dlits",
        "tabTools Transfer Dlits Item",
    ]

    for table in tables_to_drop:
        if frappe.db.table_exists(table):
            frappe.db.sql(f"DROP TABLE IF EXISTS `{table}`")
            print(f"   Dropped table: {table}")
        else:
            print(f"   Table not found (skip): {table}")

    # --- 2. Remove old DocType meta records ---
    doctypes_to_remove = [
        "DLITS Sales Partner",
        "DLITS Sales Partner Commission Entry",
        "Employee Tools Allocation",
        "Employee Tools Allocation Item",
        "Tools Transfer Dlits",
        "Tools Transfer Dlits Item",
    ]

    for dt in doctypes_to_remove:
        if frappe.db.exists("DocType", dt):
            frappe.db.sql("DELETE FROM `tabDocType` WHERE name = %s", dt)
            frappe.db.sql("DELETE FROM `tabDocField` WHERE parent = %s", dt)
            frappe.db.sql("DELETE FROM `tabDocPerm` WHERE parent = %s", dt)
            print(f"   Removed DocType record: {dt}")
        else:
            print(f"   DocType record not found (skip): {dt}")

    # --- 3. Remove old Report records ---
    reports_to_remove = [
        "DLITS Customer Ledger Report",
        "DLITS Sales Partner Commission Report",
        "DLITS Supplier Ledger Report",
        "Tools Transfer Report",
        "Pricing Rules Analysis",
    ]

    for report in reports_to_remove:
        if frappe.db.exists("Report", report):
            frappe.db.sql("DELETE FROM `tabReport` WHERE name = %s", report)
            print(f"   Removed Report record: {report}")
        else:
            print(f"   Report record not found (skip): {report}")

    # --- 4. Remove old Custom Fields from Sales Invoice and Sales Order ---
    old_custom_fields = [
        # Sales Invoice
        {"dt": "Sales Invoice", "fieldname": "dlits_commission_section"},
        {"dt": "Sales Invoice", "fieldname": "dlits_sales_partner"},
        {"dt": "Sales Invoice", "fieldname": "dlits_commission_type"},
        {"dt": "Sales Invoice", "fieldname": "dlits_commission_rate"},
        {"dt": "Sales Invoice", "fieldname": "column_break_commission"},
        {"dt": "Sales Invoice", "fieldname": "dlits_commission_amount"},
        {"dt": "Sales Invoice", "fieldname": "dlits_commission_paid_amount"},
        {"dt": "Sales Invoice", "fieldname": "dlits_commission_outstanding"},
        # Sales Order
        {"dt": "Sales Order", "fieldname": "dlits_commission_section"},
        {"dt": "Sales Order", "fieldname": "dlits_sales_partner"},
        {"dt": "Sales Order", "fieldname": "dlits_commission_type"},
        {"dt": "Sales Order", "fieldname": "dlits_commission_rate"},
        {"dt": "Sales Order", "fieldname": "column_break_commission"},
        {"dt": "Sales Order", "fieldname": "dlits_commission_amount"},
        # Legacy Sales Partner fields
        {"dt": "Sales Partner", "fieldname": "supplier"},
        {"dt": "Sales Partner", "fieldname": "auto_create_supplier"},
    ]

    for field in old_custom_fields:
        cf_name = frappe.db.get_value(
            "Custom Field", {"dt": field["dt"], "fieldname": field["fieldname"]}, "name"
        )
        if cf_name:
            frappe.db.sql("DELETE FROM `tabCustom Field` WHERE name = %s", cf_name)
            print(f"   Removed custom field: {field['fieldname']} on {field['dt']}")
        else:
            print(f"   Custom field not found (skip): {field['fieldname']} on {field['dt']}")

    # --- 5. Drop the actual columns from Sales Invoice and Sales Order ---
    column_map = {
        "Sales Invoice": [
            "dlits_commission_section",
            "dlits_sales_partner",
            "dlits_commission_type",
            "dlits_commission_rate",
            "column_break_commission",
            "dlits_commission_amount",
            "dlits_commission_paid_amount",
            "dlits_commission_outstanding",
        ],
        "Sales Order": [
            "dlits_commission_section",
            "dlits_sales_partner",
            "dlits_commission_type",
            "dlits_commission_rate",
            "column_break_commission",
            "dlits_commission_amount",
        ],
    }

    # Commit all DML (DELETE) operations before running DDL (ALTER TABLE)
    # MySQL DDL causes implicit commit — Frappe requires an explicit commit first
    frappe.db.commit()

    for doctype, columns in column_map.items():
        table = f"tab{doctype}"
        existing_columns = [
            row[0]
            for row in frappe.db.sql(f"SHOW COLUMNS FROM `{table}`")
        ]
        for col in columns:
            if col in existing_columns:
                frappe.db.sql(f"ALTER TABLE `{table}` DROP COLUMN `{col}`", auto_commit=True)
                print(f"   Dropped column: {col} from {table}")
            else:
                print(f"   Column not found (skip): {col} in {table}")
    print("=" * 50)
    print("Old features cleanup complete.")
    print("=" * 50)
