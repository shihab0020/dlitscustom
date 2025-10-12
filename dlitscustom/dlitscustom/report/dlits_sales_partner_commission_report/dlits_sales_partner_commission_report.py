# Copyright (c) 2024, DLITS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, today
from dlitscustom.utils.commission_management_dlits import get_sales_partner_commission_summary

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data, filters)
    return columns, data, None, chart

def get_columns():
    return [
        {
            "label": _("DLITS Sales Partner"),
            "fieldname": "sales_partner",
            "fieldtype": "Link",
            "options": "DLITS Sales Partner",
            "width": 150
        },
        {
            "label": _("Partner Name"),
            "fieldname": "partner_name",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Commission Rate (%)"),
            "fieldname": "commission_rate",
            "fieldtype": "Percent",
            "width": 120
        },
        {
            "label": _("Total Sales"),
            "fieldname": "total_sales",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Total Orders"),
            "fieldname": "total_orders",
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("Total Commission"),
            "fieldname": "total_commission",
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "label": _("Paid Commission"),
            "fieldname": "paid_commission",
            "fieldtype": "Currency",
            "width": 130
        },
        {
            "label": _("Outstanding Commission"),
            "fieldname": "outstanding_commission",
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "label": _("Payment Status"),
            "fieldname": "payment_status",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Linked Supplier"),
            "fieldname": "linked_supplier",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Recent Sales Invoices"),
            "fieldname": "recent_invoices",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": _("Recent Payments"),
            "fieldname": "recent_payments",
            "fieldtype": "Data",
            "width": 180
        },
        {
            "label": _("Last Transaction"),
            "fieldname": "last_transaction_date",
            "fieldtype": "Date",
            "width": 120
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    from_date = filters.get("from_date") or frappe.utils.add_months(today(), -3)
    to_date = filters.get("to_date") or today()
    
    # Get all DLITS sales partners
    sales_partners = frappe.db.sql(f"""
        SELECT
            sp.name as sales_partner,
            sp.partner_name,
            sp.commission_rate,
            sp.status,
            sp.supplier as linked_supplier
        FROM `tabDLITS Sales Partner` sp
        WHERE 1=1 {conditions}
        ORDER BY sp.partner_name
    """, as_dict=True)
    
    data = []
    
    for sp in sales_partners:
        # Get commission summary for this sales partner
        summary = get_sales_partner_commission_summary(
            sp.sales_partner, from_date, to_date
        )
        
        # Get the actual outstanding commission from DLITS Sales Partner record
        partner_record = frappe.get_doc("DLITS Sales Partner", sp.sales_partner)
        actual_outstanding = flt(partner_record.outstanding_commission or 0)
        actual_total_commission = flt(partner_record.total_commission_earned or 0)
        actual_paid_commission = flt(partner_record.total_commission_paid or 0)
        actual_total_sales = flt(partner_record.total_sales or 0)
        
        # Use the higher values between calculated and stored
        final_total_commission = max(summary['total_commission'], actual_total_commission)
        final_paid_commission = max(summary['paid_commission'], actual_paid_commission)
        final_outstanding_commission = max(summary['outstanding_commission'], actual_outstanding)
        final_total_sales = max(summary['total_sales'], actual_total_sales)
        
        # Get recent sales invoices (last 3)
        recent_invoices = frappe.db.sql("""
            SELECT name, posting_date, base_grand_total, dlits_commission_amount
            FROM `tabSales Invoice`
            WHERE dlits_sales_partner = %s AND docstatus = 1
            ORDER BY posting_date DESC
            LIMIT 3
        """, (sp.sales_partner,), as_dict=True)
        
        # Format recent invoices display
        recent_invoices_display = ""
        if recent_invoices:
            invoice_list = []
            for inv in recent_invoices:
                invoice_list.append(f"{inv.name} ({frappe.format(inv.dlits_commission_amount, {'fieldtype': 'Currency'})})")
            recent_invoices_display = ", ".join(invoice_list)
        else:
            recent_invoices_display = "No invoices found"
        
        # Get recent payments (last 3)
        recent_payments_display = "No payments found"
        if sp.linked_supplier:
            # Get supplier name for display
            supplier_name = frappe.db.get_value("Supplier", sp.linked_supplier, "supplier_name") or sp.linked_supplier
            
            recent_payments = frappe.db.sql("""
                SELECT name, reference_date, paid_amount
                FROM `tabPayment Entry`
                WHERE party_type = 'Supplier' AND party = %s AND docstatus = 1
                AND (remarks LIKE %s OR remarks LIKE %s)
                ORDER BY reference_date DESC
                LIMIT 3
            """, (sp.linked_supplier, f"%Commission%{sp.sales_partner}%", f"%commission%{sp.sales_partner}%"), as_dict=True)
            
            if recent_payments:
                payment_list = []
                for payment in recent_payments:
                    payment_list.append(f"{payment.name} ({frappe.format(payment.paid_amount, {'fieldtype': 'Currency'})})")
                recent_payments_display = ", ".join(payment_list)
        
        # Get last transaction date (only from Sales Invoices)
        last_transaction = frappe.db.sql("""
            SELECT MAX(posting_date) as last_date
            FROM `tabSales Invoice`
            WHERE dlits_sales_partner = %s AND docstatus = 1
        """, (sp.sales_partner,), as_dict=True)
        
        last_transaction_date = last_transaction[0].last_date if last_transaction and last_transaction[0].last_date else None
        
        # Determine payment status
        payment_status = get_payment_status(final_outstanding_commission, final_total_commission)
        
        # Get supplier display name
        supplier_display = "Not Linked"
        if sp.linked_supplier:
            supplier_name = frappe.db.get_value("Supplier", sp.linked_supplier, "supplier_name")
            supplier_display = supplier_name or sp.linked_supplier
        
        # Include if there's any commission (from transactions or stored) or if show_all is enabled
        if final_total_commission > 0 or final_outstanding_commission > 0 or filters.get('show_all'):
            data.append({
                "sales_partner": sp.sales_partner,
                "partner_name": sp.partner_name,
                "commission_rate": sp.commission_rate,
                "total_sales": final_total_sales,
                "total_orders": summary['total_orders'],
                "total_commission": final_total_commission,
                "paid_commission": final_paid_commission,
                "outstanding_commission": final_outstanding_commission,
                "payment_status": payment_status,
                "linked_supplier": supplier_display,
                "recent_invoices": recent_invoices_display,
                "recent_payments": recent_payments_display,
                "last_transaction_date": last_transaction_date,
                "disabled": sp.status != 'Active'
            })
    
    # Sort by outstanding commission (highest first)
    data.sort(key=lambda x: x['outstanding_commission'], reverse=True)
    
    return data

def get_conditions(filters):
    conditions = ""
    
    if not filters.get("include_disabled"):
        conditions += " AND sp.status = 'Active'"
    
    if filters.get("sales_partner"):
        conditions += f" AND sp.name = '{filters.get('sales_partner')}'"
    
    if filters.get("commission_rate_min"):
        conditions += f" AND sp.commission_rate >= {flt(filters.get('commission_rate_min'))}"
    
    if filters.get("commission_rate_max"):
        conditions += f" AND sp.commission_rate <= {flt(filters.get('commission_rate_max'))}"
    
    return conditions

def get_payment_status(outstanding, total):
    """Determine payment status based on outstanding vs total commission"""
    if total == 0:
        return "No Commission"
    elif outstanding == 0:
        return "Fully Paid"
    elif outstanding == total:
        return "Unpaid"
    else:
        return "Partially Paid"

def get_chart_data(data, filters):
    """Generate chart data for commission analysis"""
    
    if not data:
        return None
    
    # Payment Status Distribution
    status_counts = {}
    total_outstanding = 0
    total_paid = 0
    
    for row in data:
        status = row.get("payment_status", "Unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        total_outstanding += flt(row.get("outstanding_commission", 0))
        total_paid += flt(row.get("paid_commission", 0))
    
    return {
        "data": {
            "labels": ["Outstanding Commission", "Paid Commission"],
            "datasets": [
                {
                    "name": "Commission Status",
                    "values": [total_outstanding, total_paid]
                }
            ]
        },
        "type": "donut",
        "height": 300,
        "colors": ["#ff6b6b", "#51cf66"]
    }