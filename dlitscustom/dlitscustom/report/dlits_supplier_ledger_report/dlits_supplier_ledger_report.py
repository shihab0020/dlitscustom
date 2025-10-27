# Copyright (c) 2024, DLITS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, today, add_days

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data, filters)
    return columns, data, None, chart

def get_columns():
    return [
        {
            "label": _("Date"),
            "fieldname": "date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("Supplier"),
            "fieldname": "supplier",
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 150
        },
        {
            "label": _("Supplier Name"),
            "fieldname": "supplier_name",
            "fieldtype": "Data",
            "width": 150
        },
        {
            "label": _("Document Type"),
            "fieldname": "document_type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Document No"),
            "fieldname": "document_no",
            "fieldtype": "Dynamic Link",
            "options": "document_type",
            "width": 150
        },
        {
            "label": _("Description"),
            "fieldname": "description",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": _("Debit"),
            "fieldname": "debit",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Credit"),
            "fieldname": "credit",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Balance"),
            "fieldname": "balance",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Due Date"),
            "fieldname": "due_date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("Days Outstanding"),
            "fieldname": "days_outstanding",
            "fieldtype": "Int",
            "width": 120
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    from_date = filters.get("from_date") or add_days(today(), -30)
    to_date = filters.get("to_date") or today()
    
    # Get all suppliers or specific supplier
    if filters.get("supplier"):
        suppliers = [{"name": filters.get("supplier"), "supplier_name": frappe.db.get_value("Supplier", filters.get("supplier"), "supplier_name")}]
    else:
        suppliers = frappe.db.sql("""
            SELECT name, supplier_name 
            FROM `tabSupplier` 
            WHERE disabled = 0
            ORDER BY supplier_name
        """, as_dict=True)
    
    data = []
    
    for supplier in suppliers:
        supplier_data = get_supplier_ledger_data(supplier.get("name"), from_date, to_date, filters)
        if supplier_data or filters.get("show_zero_balance"):
            data.extend(supplier_data)
    
    return data

def get_supplier_ledger_data(supplier, from_date, to_date, filters):
    """Get ledger data for a specific supplier"""
    
    # Get opening balance
    opening_balance = get_opening_balance(supplier, from_date)
    
    # Get all transactions
    transactions = []
    
    # Purchase Invoices
    purchase_invoices = frappe.db.sql("""
        SELECT 
            posting_date as date,
            name as document_no,
            'Purchase Invoice' as document_type,
            supplier,
            supplier_name,
            0 as debit,
            base_grand_total as credit,
            outstanding_amount,
            status,
            due_date,
            remarks as description
        FROM `tabPurchase Invoice`
        WHERE supplier = %s
        AND docstatus = 1
        AND posting_date BETWEEN %s AND %s
        ORDER BY posting_date, creation
    """, (supplier, from_date, to_date), as_dict=True)
    
    transactions.extend(purchase_invoices)
    
    # Payment Entries (Payments to Supplier)
    payment_entries = frappe.db.sql("""
        SELECT 
            reference_date as date,
            name as document_no,
            'Payment Entry' as document_type,
            party as supplier,
            (SELECT supplier_name FROM `tabSupplier` WHERE name = pe.party) as supplier_name,
            paid_amount as debit,
            0 as credit,
            0 as outstanding_amount,
            'Paid' as status,
            reference_date as due_date,
            remarks as description
        FROM `tabPayment Entry` pe
        WHERE party_type = 'Supplier'
        AND party = %s
        AND docstatus = 1
        AND reference_date BETWEEN %s AND %s
        AND payment_type = 'Pay'
        ORDER BY reference_date, creation
    """, (supplier, from_date, to_date), as_dict=True)
    
    transactions.extend(payment_entries)
    
    # Journal Entries
    journal_entries = frappe.db.sql("""
        SELECT 
            je.posting_date as date,
            je.name as document_no,
            'Journal Entry' as document_type,
            jea.party as supplier,
            (SELECT supplier_name FROM `tabSupplier` WHERE name = jea.party) as supplier_name,
            CASE WHEN jea.debit_in_account_currency > 0 THEN jea.debit_in_account_currency ELSE 0 END as debit,
            CASE WHEN jea.credit_in_account_currency > 0 THEN jea.credit_in_account_currency ELSE 0 END as credit,
            0 as outstanding_amount,
            'Posted' as status,
            je.posting_date as due_date,
            je.user_remark as description
        FROM `tabJournal Entry` je
        INNER JOIN `tabJournal Entry Account` jea ON je.name = jea.parent
        WHERE jea.party_type = 'Supplier'
        AND jea.party = %s
        AND je.docstatus = 1
        AND je.posting_date BETWEEN %s AND %s
        ORDER BY je.posting_date, je.creation
    """, (supplier, from_date, to_date), as_dict=True)
    
    transactions.extend(journal_entries)
    
    # Sort all transactions by date
    transactions.sort(key=lambda x: (x.date, x.document_no))
    
    # Calculate running balance and prepare final data
    ledger_data = []
    running_balance = opening_balance
    
    # Add opening balance row if there are transactions or if opening balance is not zero
    if transactions or opening_balance != 0:
        supplier_name = frappe.db.get_value("Supplier", supplier, "supplier_name")
        
        if opening_balance != 0:
            ledger_data.append({
                "date": from_date,
                "supplier": supplier,
                "supplier_name": supplier_name,
                "document_type": "Opening Balance",
                "document_no": "",
                "description": "Opening Balance",
                "debit": abs(opening_balance) if opening_balance < 0 else 0,
                "credit": opening_balance if opening_balance > 0 else 0,
                "balance": opening_balance,
                "status": "",
                "due_date": "",
                "days_outstanding": ""
            })
    
    # Process each transaction
    for transaction in transactions:
        debit = flt(transaction.get("debit", 0))
        credit = flt(transaction.get("credit", 0))
        running_balance += credit - debit  # For suppliers: credit increases balance, debit decreases
        
        # Calculate days outstanding for invoices
        days_outstanding = ""
        if transaction.document_type == "Purchase Invoice" and transaction.outstanding_amount > 0:
            if transaction.due_date:
                days_outstanding = (getdate(today()) - getdate(transaction.due_date)).days
                if days_outstanding < 0:
                    days_outstanding = 0
        
        ledger_data.append({
            "date": transaction.date,
            "supplier": transaction.supplier,
            "supplier_name": transaction.supplier_name,
            "document_type": transaction.document_type,
            "document_no": transaction.document_no,
            "description": transaction.description or transaction.document_type,
            "debit": debit,
            "credit": credit,
            "balance": running_balance,
            "status": transaction.status,
            "due_date": transaction.due_date,
            "days_outstanding": days_outstanding
        })
    
    # Add closing balance row
    if ledger_data:
        ledger_data.append({
            "date": to_date,
            "supplier": supplier,
            "supplier_name": supplier_name,
            "document_type": "Closing Balance",
            "document_no": "",
            "description": "Closing Balance",
            "debit": 0,
            "credit": 0,
            "balance": running_balance,
            "status": "",
            "due_date": "",
            "days_outstanding": ""
        })
    
    return ledger_data

def get_opening_balance(supplier, from_date):
    """Calculate opening balance for supplier before from_date"""
    
    # Get total invoices before from_date
    invoice_total = frappe.db.sql("""
        SELECT COALESCE(SUM(base_grand_total), 0) as total
        FROM `tabPurchase Invoice`
        WHERE supplier = %s
        AND docstatus = 1
        AND posting_date < %s
    """, (supplier, from_date))[0][0] or 0
    
    # Get total payments before from_date
    payment_total = frappe.db.sql("""
        SELECT COALESCE(SUM(paid_amount), 0) as total
        FROM `tabPayment Entry`
        WHERE party_type = 'Supplier'
        AND party = %s
        AND docstatus = 1
        AND reference_date < %s
        AND payment_type = 'Pay'
    """, (supplier, from_date))[0][0] or 0
    
    # Get journal entry adjustments before from_date
    journal_total = frappe.db.sql("""
        SELECT 
            COALESCE(SUM(jea.credit_in_account_currency), 0) - COALESCE(SUM(jea.debit_in_account_currency), 0) as total
        FROM `tabJournal Entry` je
        INNER JOIN `tabJournal Entry Account` jea ON je.name = jea.parent
        WHERE jea.party_type = 'Supplier'
        AND jea.party = %s
        AND je.docstatus = 1
        AND je.posting_date < %s
    """, (supplier, from_date))[0][0] or 0
    
    return flt(invoice_total) - flt(payment_total) + flt(journal_total)

def get_conditions(filters):
    conditions = ""
    
    if filters.get("company"):
        conditions += f" AND company = '{filters.get('company')}'"
    
    if filters.get("supplier_group"):
        conditions += f" AND supplier_group = '{filters.get('supplier_group')}'"
    
    return conditions

def get_chart_data(data, filters):
    """Generate chart data for supplier ledger analysis"""
    
    if not data:
        return None
    
    # Calculate summary data
    total_debit = sum(flt(row.get("debit", 0)) for row in data if row.get("document_type") not in ["Opening Balance", "Closing Balance"])
    total_credit = sum(flt(row.get("credit", 0)) for row in data if row.get("document_type") not in ["Opening Balance", "Closing Balance"])
    
    # Get outstanding amounts by age
    outstanding_data = {"0-30": 0, "31-60": 0, "61-90": 0, "90+": 0}
    
    for row in data:
        if row.get("document_type") == "Purchase Invoice" and row.get("days_outstanding"):
            days = int(row.get("days_outstanding", 0))
            outstanding_amount = flt(row.get("credit", 0)) - flt(row.get("debit", 0))
            
            if days <= 30:
                outstanding_data["0-30"] += outstanding_amount
            elif days <= 60:
                outstanding_data["31-60"] += outstanding_amount
            elif days <= 90:
                outstanding_data["61-90"] += outstanding_amount
            else:
                outstanding_data["90+"] += outstanding_amount
    
    return {
        "data": {
            "labels": ["Total Purchases", "Total Payments", "Outstanding 0-30", "Outstanding 31-60", "Outstanding 61-90", "Outstanding 90+"],
            "datasets": [
                {
                    "name": "Supplier Ledger Analysis",
                    "values": [total_credit, total_debit, outstanding_data["0-30"], outstanding_data["31-60"], outstanding_data["61-90"], outstanding_data["90+"]]
                }
            ]
        },
        "type": "bar",
        "height": 300,
        "colors": ["#dc3545", "#28a745", "#ffc107", "#fd7e14", "#dc3545", "#6f42c1"]
    }