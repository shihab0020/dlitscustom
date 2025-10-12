# Copyright (c) 2024, DLITS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, formatdate, add_days
from datetime import datetime

def execute(filters=None):
    if not filters:
        filters = {}
    
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data, filters)
    
    return columns, data, None, chart

def get_columns():
    return [
        {
            "label": _("Tax Account"),
            "fieldname": "tax_account",
            "fieldtype": "Link",
            "options": "Account",
            "width": 200
        },
        {
            "label": _("Tax Rate (%)"),
            "fieldname": "tax_rate",
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "label": _("Transaction Type"),
            "fieldname": "transaction_type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Document"),
            "fieldname": "document",
            "fieldtype": "Dynamic Link",
            "options": "document_type",
            "width": 150
        },
        {
            "label": _("Document Type"),
            "fieldname": "document_type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("Customer/Supplier"),
            "fieldname": "party",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": _("Net Amount"),
            "fieldname": "net_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Tax Amount"),
            "fieldname": "tax_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Total Amount"),
            "fieldname": "total_amount",
            "fieldtype": "Currency",
            "width": 120
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    # Get Sales Invoice Tax Data
    sales_tax_data = frappe.db.sql("""
        SELECT 
            stc.account_head as tax_account,
            stc.rate as tax_rate,
            'Sales' as transaction_type,
            si.name as document,
            'Sales Invoice' as document_type,
            si.posting_date,
            si.customer as party,
            si.net_total as net_amount,
            stc.tax_amount,
            si.grand_total as total_amount
        FROM `tabSales Taxes and Charges` stc
        INNER JOIN `tabSales Invoice` si ON stc.parent = si.name
        WHERE si.docstatus = 1 {sales_conditions}
        ORDER BY si.posting_date DESC, stc.rate DESC
    """.format(sales_conditions=conditions.get('sales', '')), filters, as_dict=1)
    
    # Get Purchase Invoice Tax Data
    purchase_tax_data = frappe.db.sql("""
        SELECT 
            ptc.account_head as tax_account,
            ptc.rate as tax_rate,
            'Purchase' as transaction_type,
            pi.name as document,
            'Purchase Invoice' as document_type,
            pi.posting_date,
            pi.supplier as party,
            pi.net_total as net_amount,
            ptc.tax_amount,
            pi.grand_total as total_amount
        FROM `tabPurchase Taxes and Charges` ptc
        INNER JOIN `tabPurchase Invoice` pi ON ptc.parent = pi.name
        WHERE pi.docstatus = 1 {purchase_conditions}
        ORDER BY pi.posting_date DESC, ptc.rate DESC
    """.format(purchase_conditions=conditions.get('purchase', '')), filters, as_dict=1)
    
    # Combine and sort data
    all_data = sales_tax_data + purchase_tax_data
    
    # Sort by date (newest first) and then by tax rate
    all_data.sort(key=lambda x: (x.posting_date, x.tax_rate), reverse=True)
    
    # Add summary rows
    summary_data = get_summary_data(all_data)
    
    return summary_data + all_data

def get_conditions(filters):
    conditions = {'sales': '', 'purchase': ''}
    
    if filters.get("from_date"):
        conditions['sales'] += " AND si.posting_date >= %(from_date)s"
        conditions['purchase'] += " AND pi.posting_date >= %(from_date)s"
    
    if filters.get("to_date"):
        conditions['sales'] += " AND si.posting_date <= %(to_date)s"
        conditions['purchase'] += " AND pi.posting_date <= %(to_date)s"
    
    if filters.get("tax_account"):
        conditions['sales'] += " AND stc.account_head = %(tax_account)s"
        conditions['purchase'] += " AND ptc.account_head = %(tax_account)s"
    
    if filters.get("tax_rate"):
        conditions['sales'] += " AND stc.rate = %(tax_rate)s"
        conditions['purchase'] += " AND ptc.rate = %(tax_rate)s"
    
    if filters.get("transaction_type"):
        if filters.get("transaction_type") == "Sales":
            conditions['purchase'] = " AND 1=0"  # Exclude purchase data
        elif filters.get("transaction_type") == "Purchase":
            conditions['sales'] = " AND 1=0"  # Exclude sales data
    
    if filters.get("customer"):
        conditions['sales'] += " AND si.customer = %(customer)s"
    
    if filters.get("supplier"):
        conditions['purchase'] += " AND pi.supplier = %(supplier)s"
    
    return conditions

def get_summary_data(data):
    if not data:
        return []
    
    # Group by tax account and rate
    tax_summary = {}
    sales_total = 0
    purchase_total = 0
    
    for row in data:
        key = f"{row.tax_account}_{row.tax_rate}"
        if key not in tax_summary:
            tax_summary[key] = {
                'tax_account': row.tax_account,
                'tax_rate': row.tax_rate,
                'sales_amount': 0,
                'purchase_amount': 0,
                'net_amount': 0,
                'total_tax': 0
            }
        
        if row.transaction_type == 'Sales':
            tax_summary[key]['sales_amount'] += flt(row.tax_amount)
            sales_total += flt(row.tax_amount)
        else:
            tax_summary[key]['purchase_amount'] += flt(row.tax_amount)
            purchase_total += flt(row.tax_amount)
        
        tax_summary[key]['total_tax'] += flt(row.tax_amount)
    
    # Create summary rows
    summary_rows = []
    
    # Overall summary
    summary_rows.append({
        'tax_account': '<b>TOTAL TAX SUMMARY</b>',
        'tax_rate': '',
        'transaction_type': '',
        'document': '',
        'document_type': '',
        'posting_date': '',
        'party': '',
        'net_amount': '',
        'tax_amount': f'<b>{sales_total + purchase_total:.2f}</b>',
        'total_amount': ''
    })
    
    summary_rows.append({
        'tax_account': 'Sales Tax Total',
        'tax_rate': '',
        'transaction_type': 'Sales',
        'document': '',
        'document_type': '',
        'posting_date': '',
        'party': '',
        'net_amount': '',
        'tax_amount': f'{sales_total:.2f}',
        'total_amount': ''
    })
    
    summary_rows.append({
        'tax_account': 'Purchase Tax Total',
        'tax_rate': '',
        'transaction_type': 'Purchase',
        'document': '',
        'document_type': '',
        'posting_date': '',
        'party': '',
        'net_amount': '',
        'tax_amount': f'{purchase_total:.2f}',
        'total_amount': ''
    })
    
    # Add separator
    summary_rows.append({
        'tax_account': '─' * 50,
        'tax_rate': '',
        'transaction_type': '',
        'document': '',
        'document_type': '',
        'posting_date': '',
        'party': '',
        'net_amount': '',
        'tax_amount': '',
        'total_amount': ''
    })
    
    return summary_rows

def get_chart_data(data, filters):
    if not data:
        return None
    
    # Filter out summary rows for chart
    chart_data = [row for row in data if not (
        row.get('tax_account', '').startswith('<b>') or 
        row.get('tax_account', '').startswith('Sales Tax Total') or
        row.get('tax_account', '').startswith('Purchase Tax Total') or
        '─' in str(row.get('tax_account', ''))
    )]
    
    if not chart_data:
        return None
    
    # Group by transaction type
    sales_total = sum(flt(row.tax_amount) for row in chart_data if row.transaction_type == 'Sales')
    purchase_total = sum(flt(row.tax_amount) for row in chart_data if row.transaction_type == 'Purchase')
    
    return {
        "data": {
            "labels": ["Sales Tax", "Purchase Tax"],
            "datasets": [
                {
                    "name": "Tax Amount",
                    "values": [sales_total, purchase_total]
                }
            ]
        },
        "type": "donut",
        "height": 300,
        "colors": ["#28a745", "#dc3545"]
    }