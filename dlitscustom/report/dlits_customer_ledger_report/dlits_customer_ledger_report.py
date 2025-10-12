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
            "fieldname": "customer",
            "label": _("Customer"),
            "fieldtype": "Link",
            "options": "Customer",
            "width": 150
        },
        {
            "fieldname": "customer_name",
            "label": _("Customer Name"),
            "fieldtype": "Data",
            "width": 200
        },
        {
            "fieldname": "total_invoiced",
            "label": _("Total Invoiced"),
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
            "fieldname": "recent_invoices",
            "label": _("Recent Invoices"),
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
    
    # Get customer data with invoices and payments
    query = """
        SELECT 
            c.name as customer,
            c.customer_name,
            COALESCE(SUM(si.grand_total), 0) as total_invoiced,
            COALESCE(SUM(si.paid_amount), 0) as total_paid,
            COALESCE(SUM(si.outstanding_amount), 0) as outstanding_amount
        FROM `tabCustomer` c
        LEFT JOIN `tabSales Invoice` si ON c.name = si.customer 
            AND si.docstatus = 1 {conditions}
        GROUP BY c.name, c.customer_name
        HAVING total_invoiced > 0 OR outstanding_amount > 0
        ORDER BY outstanding_amount DESC, total_invoiced DESC
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
        conditions += " AND si.posting_date >= %(from_date)s"
    
    if filters.get("to_date"):
        conditions += " AND si.posting_date <= %(to_date)s"
    
    if filters.get("customer"):
        conditions += " AND c.name = %(customer)s"
    
    return conditions

def add_aging_analysis(row, filters):
    """Add aging analysis for outstanding amounts"""
    customer = row.get("customer")
    to_date = filters.get("to_date") or frappe.utils.today()
    
    aging_query = """
        SELECT 
            SUM(CASE 
                WHEN DATEDIFF(%(to_date)s, si.posting_date) <= 30 
                THEN si.outstanding_amount ELSE 0 
            END) as aging_0_30,
            SUM(CASE 
                WHEN DATEDIFF(%(to_date)s, si.posting_date) BETWEEN 31 AND 60 
                THEN si.outstanding_amount ELSE 0 
            END) as aging_31_60,
            SUM(CASE 
                WHEN DATEDIFF(%(to_date)s, si.posting_date) BETWEEN 61 AND 90 
                THEN si.outstanding_amount ELSE 0 
            END) as aging_61_90,
            SUM(CASE 
                WHEN DATEDIFF(%(to_date)s, si.posting_date) > 90 
                THEN si.outstanding_amount ELSE 0 
            END) as aging_over_90
        FROM `tabSales Invoice` si
        WHERE si.customer = %(customer)s 
            AND si.docstatus = 1 
            AND si.outstanding_amount > 0
    """
    
    aging_data = frappe.db.sql(aging_query, {
        "customer": customer,
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
    """Add recent invoices and payments information"""
    customer = row.get("customer")
    
    # Recent invoices
    recent_invoices = frappe.db.sql("""
        SELECT name, posting_date, grand_total
        FROM `tabSales Invoice`
        WHERE customer = %(customer)s AND docstatus = 1
        ORDER BY posting_date DESC
        LIMIT 3
    """, {"customer": customer}, as_dict=True)
    
    invoice_list = []
    for inv in recent_invoices:
        invoice_list.append(f"{inv.name} ({formatdate(inv.posting_date)}: {frappe.format_value(inv.grand_total, 'Currency')})")
    
    row["recent_invoices"] = "; ".join(invoice_list) if invoice_list else "No recent invoices"
    
    # Recent payments
    recent_payments = frappe.db.sql("""
        SELECT pe.name, pe.posting_date, pe.paid_amount
        FROM `tabPayment Entry` pe
        WHERE pe.party = %(customer)s 
            AND pe.party_type = 'Customer'
            AND pe.docstatus = 1
        ORDER BY pe.posting_date DESC
        LIMIT 3
    """, {"customer": customer}, as_dict=True)
    
    payment_list = []
    for pay in recent_payments:
        payment_list.append(f"{pay.name} ({formatdate(pay.posting_date)}: {frappe.format_value(pay.paid_amount, 'Currency')})")
    
    row["recent_payments"] = "; ".join(payment_list) if payment_list else "No recent payments"

def get_chart_data(data, filters):
    """Generate chart data for customer ledger analysis"""
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