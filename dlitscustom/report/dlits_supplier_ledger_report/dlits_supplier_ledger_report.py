# Copyright (c) 2024, DLITS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, formatdate, add_days
from datetime import datetime, timedelta

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data, filters)
    
    return columns, data, None, chart

def get_columns():
    return [
        {
            "fieldname": "supplier",
            "label": _("Supplier"),
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 150
        },
        {
            "fieldname": "supplier_name",
            "label": _("Supplier Name"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "total_billed",
            "label": _("Total Billed"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "total_paid",
            "label": _("Total Paid"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "outstanding_amount",
            "label": _("Outstanding"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "aging_0_30",
            "label": _("0-30 Days"),
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "fieldname": "aging_31_60",
            "label": _("31-60 Days"),
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "fieldname": "aging_61_90",
            "label": _("61-90 Days"),
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "fieldname": "aging_over_90",
            "label": _("Over 90 Days"),
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "fieldname": "recent_bills",
            "label": _("Recent Bills"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "recent_payments",
            "label": _("Recent Payments"),
            "fieldtype": "Data",
            "width": 200
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    # Get supplier data with purchase invoices and payments
    query = """
        SELECT 
            s.name as supplier,
            s.supplier_name,
            COALESCE(SUM(pi.grand_total), 0) as total_billed,
            COALESCE(SUM(pi.paid_amount), 0) as total_paid,
            COALESCE(SUM(pi.outstanding_amount), 0) as outstanding_amount
        FROM `tabSupplier` s
        LEFT JOIN `tabPurchase Invoice` pi ON s.name = pi.supplier 
            AND pi.docstatus = 1 {conditions}
        GROUP BY s.name, s.supplier_name
        HAVING total_billed > 0 OR outstanding_amount > 0
        ORDER BY outstanding_amount DESC, total_billed DESC
    """.format(conditions=conditions)
    
    data = frappe.db.sql(query, filters, as_dict=True)
    
    # Add aging analysis and recent transactions
    for row in data:
        add_aging_analysis(row, filters)
        add_recent_transactions(row, filters)
    
    return data

def get_conditions(filters):
    conditions = ""
    
    if filters.get("from_date"):
        conditions += " AND pi.posting_date >= %(from_date)s"
    
    if filters.get("to_date"):
        conditions += " AND pi.posting_date <= %(to_date)s"
    
    if filters.get("supplier"):
        conditions += " AND s.name = %(supplier)s"
    
    return conditions

def add_aging_analysis(row, filters):
    """Add aging analysis for outstanding amounts"""
    supplier = row.get("supplier")
    to_date = filters.get("to_date") or frappe.utils.today()
    
    aging_query = """
        SELECT 
            SUM(CASE 
                WHEN DATEDIFF(%(to_date)s, pi.posting_date) <= 30 
                THEN pi.outstanding_amount ELSE 0 
            END) as aging_0_30,
            SUM(CASE 
                WHEN DATEDIFF(%(to_date)s, pi.posting_date) BETWEEN 31 AND 60 
                THEN pi.outstanding_amount ELSE 0 
            END) as aging_31_60,
            SUM(CASE 
                WHEN DATEDIFF(%(to_date)s, pi.posting_date) BETWEEN 61 AND 90 
                THEN pi.outstanding_amount ELSE 0 
            END) as aging_61_90,
            SUM(CASE 
                WHEN DATEDIFF(%(to_date)s, pi.posting_date) > 90 
                THEN pi.outstanding_amount ELSE 0 
            END) as aging_over_90
        FROM `tabPurchase Invoice` pi
        WHERE pi.supplier = %(supplier)s 
            AND pi.docstatus = 1 
            AND pi.outstanding_amount > 0
    """
    
    aging_data = frappe.db.sql(aging_query, {
        "supplier": supplier,
        "to_date": to_date
    }, as_dict=True)
    
    if aging_data:
        aging = aging_data[0]
        row.update({
            "aging_0_30": flt(aging.get("aging_0_30", 0)),
            "aging_31_60": flt(aging.get("aging_31_60", 0)),
            "aging_61_90": flt(aging.get("aging_61_90", 0)),
            "aging_over_90": flt(aging.get("aging_over_90", 0))
        })

def add_recent_transactions(row, filters):
    """Add recent bills and payments information"""
    supplier = row.get("supplier")
    
    # Recent bills
    recent_bills = frappe.db.sql("""
        SELECT name, posting_date, grand_total
        FROM `tabPurchase Invoice`
        WHERE supplier = %(supplier)s AND docstatus = 1
        ORDER BY posting_date DESC
        LIMIT 3
    """, {"supplier": supplier}, as_dict=True)
    
    bill_list = []
    for bill in recent_bills:
        bill_list.append(f"{bill.name} ({formatdate(bill.posting_date)}: {frappe.format_value(bill.grand_total, 'Currency')})")
    
    row["recent_bills"] = "; ".join(bill_list) if bill_list else "No recent bills"
    
    # Recent payments
    recent_payments = frappe.db.sql("""
        SELECT pe.name, pe.posting_date, pe.paid_amount
        FROM `tabPayment Entry` pe
        WHERE pe.party = %(supplier)s 
            AND pe.party_type = 'Supplier'
            AND pe.docstatus = 1
        ORDER BY pe.posting_date DESC
        LIMIT 3
    """, {"supplier": supplier}, as_dict=True)
    
    payment_list = []
    for pay in recent_payments:
        payment_list.append(f"{pay.name} ({formatdate(pay.posting_date)}: {frappe.format_value(pay.paid_amount, 'Currency')})")
    
    row["recent_payments"] = "; ".join(payment_list) if payment_list else "No recent payments"

def get_chart_data(data, filters):
    """Generate chart data for supplier ledger analysis"""
    if not data:
        return None
    
    # Aging analysis chart
    aging_labels = ["0-30 Days", "31-60 Days", "61-90 Days", "Over 90 Days"]
    aging_values = [0, 0, 0, 0]
    
    for row in data:
        aging_values[0] += flt(row.get("aging_0_30", 0))
        aging_values[1] += flt(row.get("aging_31_60", 0))
        aging_values[2] += flt(row.get("aging_61_90", 0))
        aging_values[3] += flt(row.get("aging_over_90", 0))
    
    return {
        "data": {
            "labels": aging_labels,
            "datasets": [{
                "name": "Outstanding Amount",
                "values": aging_values
            }]
        },
        "type": "donut",
        "height": 300,
        "colors": ["#28a745", "#ffc107", "#fd7e14", "#dc3545"]
    }