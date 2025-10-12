# Copyright (c) 2024, DLITS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, formatdate
from datetime import datetime, timedelta

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data, filters)
    
    return columns, data, None, chart

def get_columns():
    return [
        {
            "fieldname": "tax_type",
            "label": _("Tax Type"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "tax_rate",
            "label": _("Tax Rate (%)"),
            "fieldtype": "Percent",
            "width": 100
        },
        {
            "fieldname": "sales_tax_amount",
            "label": _("Sales Tax"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "purchase_tax_amount",
            "label": _("Purchase Tax"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "net_tax_amount",
            "label": _("Net Tax"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "sales_base_amount",
            "label": _("Sales Base Amount"),
            "fieldtype": "Currency",
            "width": 140
        },
        {
            "fieldname": "purchase_base_amount",
            "label": _("Purchase Base Amount"),
            "fieldtype": "Currency",
            "width": 140
        },
        {
            "fieldname": "sales_invoices_count",
            "label": _("Sales Invoices"),
            "fieldtype": "Int",
            "width": 100
        },
        {
            "fieldname": "purchase_invoices_count",
            "label": _("Purchase Invoices"),
            "fieldtype": "Int",
            "width": 120
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    # Get sales tax data
    sales_tax_query = """
        SELECT 
            st.account_head as tax_account,
            st.rate as tax_rate,
            SUM(st.tax_amount) as tax_amount,
            SUM(st.base_tax_amount) as base_tax_amount,
            COUNT(DISTINCT si.name) as invoice_count,
            'Sales' as tax_type_source
        FROM `tabSales Taxes and Charges` st
        INNER JOIN `tabSales Invoice` si ON st.parent = si.name
        WHERE si.docstatus = 1 {conditions}
        GROUP BY st.account_head, st.rate
    """.format(conditions=conditions.replace("pi.", "si."))
    
    sales_tax_data = frappe.db.sql(sales_tax_query, filters, as_dict=True)
    
    # Get purchase tax data
    purchase_tax_query = """
        SELECT 
            pt.account_head as tax_account,
            pt.rate as tax_rate,
            SUM(pt.tax_amount) as tax_amount,
            SUM(pt.base_tax_amount) as base_tax_amount,
            COUNT(DISTINCT pi.name) as invoice_count,
            'Purchase' as tax_type_source
        FROM `tabPurchase Taxes and Charges` pt
        INNER JOIN `tabPurchase Invoice` pi ON pt.parent = pi.name
        WHERE pi.docstatus = 1 {conditions}
        GROUP BY pt.account_head, pt.rate
    """.format(conditions=conditions)
    
    purchase_tax_data = frappe.db.sql(purchase_tax_query, filters, as_dict=True)
    
    # Combine and process data
    tax_summary = {}
    
    # Process sales tax data
    for row in sales_tax_data:
        key = f"{row.tax_account}_{row.tax_rate}"
        if key not in tax_summary:
            tax_summary[key] = {
                "tax_type": get_tax_account_name(row.tax_account),
                "tax_rate": flt(row.tax_rate),
                "sales_tax_amount": 0,
                "purchase_tax_amount": 0,
                "sales_base_amount": 0,
                "purchase_base_amount": 0,
                "sales_invoices_count": 0,
                "purchase_invoices_count": 0
            }
        
        tax_summary[key]["sales_tax_amount"] += flt(row.base_tax_amount)
        tax_summary[key]["sales_base_amount"] += flt(row.base_tax_amount) / (flt(row.tax_rate) / 100) if flt(row.tax_rate) > 0 else 0
        tax_summary[key]["sales_invoices_count"] += flt(row.invoice_count)
    
    # Process purchase tax data
    for row in purchase_tax_data:
        key = f"{row.tax_account}_{row.tax_rate}"
        if key not in tax_summary:
            tax_summary[key] = {
                "tax_type": get_tax_account_name(row.tax_account),
                "tax_rate": flt(row.tax_rate),
                "sales_tax_amount": 0,
                "purchase_tax_amount": 0,
                "sales_base_amount": 0,
                "purchase_base_amount": 0,
                "sales_invoices_count": 0,
                "purchase_invoices_count": 0
            }
        
        tax_summary[key]["purchase_tax_amount"] += flt(row.base_tax_amount)
        tax_summary[key]["purchase_base_amount"] += flt(row.base_tax_amount) / (flt(row.tax_rate) / 100) if flt(row.tax_rate) > 0 else 0
        tax_summary[key]["purchase_invoices_count"] += flt(row.invoice_count)
    
    # Calculate net tax and convert to list
    data = []
    for key, values in tax_summary.items():
        values["net_tax_amount"] = flt(values["sales_tax_amount"]) - flt(values["purchase_tax_amount"])
        data.append(values)
    
    # Sort by tax rate and tax type
    data.sort(key=lambda x: (x["tax_rate"], x["tax_type"]))
    
    return data

def get_conditions(filters):
    conditions = ""
    
    if filters.get("from_date"):
        conditions += " AND pi.posting_date >= %(from_date)s"
    
    if filters.get("to_date"):
        conditions += " AND pi.posting_date <= %(to_date)s"
    
    if filters.get("tax_type"):
        conditions += " AND pt.account_head LIKE %(tax_type)s"
    
    return conditions

def get_tax_account_name(account_head):
    """Get a clean tax account name"""
    if not account_head:
        return "Unknown Tax"
    
    # Remove common prefixes and suffixes to get clean name
    clean_name = account_head.replace("VAT", "").replace("Tax", "").replace("Taxes", "")
    clean_name = clean_name.replace(" - ", "").strip()
    
    if not clean_name:
        return account_head
    
    return clean_name

def get_chart_data(data, filters):
    """Generate chart data for tax analysis"""
    if not data:
        return None
    
    # Tax distribution chart
    labels = []
    sales_values = []
    purchase_values = []
    
    for row in data:
        label = f"{row['tax_type']} ({row['tax_rate']}%)"
        labels.append(label)
        sales_values.append(flt(row["sales_tax_amount"]))
        purchase_values.append(flt(row["purchase_tax_amount"]))
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Sales Tax",
                    "values": sales_values
                },
                {
                    "name": "Purchase Tax", 
                    "values": purchase_values
                }
            ]
        },
        "type": "bar",
        "height": 300,
        "colors": ["#28a745", "#dc3545"]
    }