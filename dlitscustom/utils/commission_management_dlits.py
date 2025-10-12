import frappe
from frappe import _
from frappe.utils import flt, getdate, today

@frappe.whitelist()
def get_sales_partner_commission_summary(sales_partner, from_date=None, to_date=None):
    """
    Get commission summary for a sales partner
    """
    if not from_date:
        from_date = frappe.utils.add_months(today(), -1)
    if not to_date:
        to_date = today()
    
    # Get commission from Sales Invoices ONLY (using dlits_sales_partner field)
    # Note: We only count from Sales Invoices to avoid double counting with Sales Orders
    si_commission = frappe.db.sql("""
        SELECT
            SUM(dlits_commission_amount) as total_commission,
            COUNT(*) as invoice_count,
            SUM(base_grand_total) as total_sales
        FROM `tabSales Invoice`
        WHERE dlits_sales_partner = %s
        AND docstatus = 1
        AND posting_date BETWEEN %s AND %s
    """, (sales_partner, from_date, to_date), as_dict=True)
    
    # Note: We no longer count Sales Orders since we only consider Sales Invoices for commission
    # This ensures consistency with our commission-only-from-invoices approach
    
    # Get paid commission (from Payment Entries only - avoid double counting)
    linked_supplier = frappe.db.get_value("Supplier", {"sales_partner_link": sales_partner}, "name")
    paid_commission = 0
    
    # Use a single comprehensive query to avoid double counting
    if linked_supplier:
        # Get all payments to linked supplier with commission references
        supplier_payments = frappe.db.sql("""
            SELECT DISTINCT pe.name, pe.paid_amount
            FROM `tabPayment Entry` pe
            WHERE pe.party_type = 'Supplier'
            AND pe.party = %s
            AND pe.docstatus = 1
            AND pe.reference_date BETWEEN %s AND %s
            AND (pe.remarks LIKE %s OR pe.remarks LIKE %s OR pe.reference_no LIKE %s)
        """, (linked_supplier, from_date, to_date,
              f"%Commission payment for Sales Partner: {sales_partner}%",
              f"%Commission%{sales_partner}%",
              f"%Commission-{sales_partner}%"), as_dict=True)
        
        # Sum up the distinct payments
        for payment in supplier_payments:
            paid_commission += flt(payment.paid_amount)
    
    else:
        # Fallback: Check payments directly to sales partner (when no supplier linked)
        partner_name = frappe.db.get_value("DLITS Sales Partner", sales_partner, "partner_name")
        if partner_name:
            direct_partner_payments = frappe.db.sql("""
                SELECT DISTINCT pe.name, pe.paid_amount
                FROM `tabPayment Entry` pe
                WHERE pe.docstatus = 1
                AND pe.reference_date BETWEEN %s AND %s
                AND (pe.party = %s OR pe.remarks LIKE %s OR pe.reference_no LIKE %s)
            """, (from_date, to_date,
                  f"{sales_partner} (Sales Partner)",
                  f"%Commission%{sales_partner}%",
                  f"%Commission-{sales_partner}%"), as_dict=True)
            
            # Sum up the distinct payments
            for payment in direct_partner_payments:
                paid_commission += flt(payment.paid_amount)
    
    # Calculate totals (only from Sales Invoices to avoid double counting)
    total_commission = flt(si_commission[0].total_commission or 0)
    total_orders = si_commission[0].invoice_count or 0  # Only count Sales Invoices
    total_sales = flt(si_commission[0].total_sales or 0)
    outstanding_commission = total_commission - paid_commission
    
    # Get supplier name if linked_supplier exists
    supplier_name = None
    if linked_supplier:
        supplier_name = frappe.db.get_value("Supplier", linked_supplier, "supplier_name") or linked_supplier
    
    return {
        "sales_partner": sales_partner,
        "from_date": from_date,
        "to_date": to_date,
        "total_commission": total_commission,
        "paid_commission": paid_commission,
        "outstanding_commission": outstanding_commission,
        "total_orders": total_orders,
        "total_sales": total_sales,
        "linked_supplier": supplier_name or "Not Linked",
        "linked_supplier_id": linked_supplier,
        "commission_rate": get_sales_partner_commission_rate(sales_partner)
    }

@frappe.whitelist()
def get_sales_partner_commission_details(sales_partner, from_date=None, to_date=None):
    """
    Get detailed commission breakdown for a sales partner
    """
    if not from_date:
        from_date = frappe.utils.add_months(today(), -1)
    if not to_date:
        to_date = today()
    
    # Get Sales Orders with commission
    sales_orders = frappe.db.sql("""
        SELECT 
            name,
            transaction_date,
            customer,
            base_grand_total,
            dlits_commission_amount as total_commission,
            dlits_commission_rate as commission_rate,
            'Sales Order' as document_type
        FROM `tabSales Order`
        WHERE dlits_sales_partner = %s 
        AND docstatus = 1
        AND transaction_date BETWEEN %s AND %s
        AND dlits_commission_amount > 0
        ORDER BY transaction_date DESC
    """, (sales_partner, from_date, to_date), as_dict=True)
    
    # Get Sales Invoices with commission
    sales_invoices = frappe.db.sql("""
        SELECT 
            name,
            posting_date as transaction_date,
            customer,
            base_grand_total,
            dlits_commission_amount as total_commission,
            dlits_commission_rate as commission_rate,
            'Sales Invoice' as document_type
        FROM `tabSales Invoice`
        WHERE dlits_sales_partner = %s 
        AND docstatus = 1
        AND posting_date BETWEEN %s AND %s
        AND dlits_commission_amount > 0
        ORDER BY posting_date DESC
    """, (sales_partner, from_date, to_date), as_dict=True)
    
    # Combine and sort by date
    all_transactions = sales_orders + sales_invoices
    all_transactions.sort(key=lambda x: x.transaction_date, reverse=True)
    
    return all_transactions

@frappe.whitelist()
def get_sales_partner_payment_history(sales_partner, from_date=None, to_date=None):
    """
    Get payment history for a sales partner including Journal Entry references
    """
    if not from_date:
        from_date = frappe.utils.add_months(today(), -12)  # Last 12 months
    if not to_date:
        to_date = today()
    
    linked_supplier = frappe.db.get_value("Supplier", {"sales_partner_link": sales_partner}, "name")
    
    if not linked_supplier:
        return []
    
    # Get direct payment entries
    direct_payments = frappe.db.sql("""
        SELECT
            name,
            reference_date,
            paid_amount,
            remarks,
            mode_of_payment,
            reference_no,
            'Direct Payment' as payment_type
        FROM `tabPayment Entry`
        WHERE party_type = 'Supplier'
        AND party = %s
        AND docstatus = 1
        AND reference_date BETWEEN %s AND %s
        ORDER BY reference_date DESC
    """, (linked_supplier, from_date, to_date), as_dict=True)
    
    # Get payments that reference Journal Entries for commissions
    journal_referenced_payments = frappe.db.sql("""
        SELECT
            pe.name,
            pe.reference_date,
            per.allocated_amount as paid_amount,
            CONCAT('Payment against Journal Entry: ', per.reference_name, ' - ', je.user_remark) as remarks,
            pe.mode_of_payment,
            pe.reference_no,
            'Journal Entry Payment' as payment_type,
            per.reference_name as journal_entry
        FROM `tabPayment Entry` pe
        INNER JOIN `tabPayment Entry Reference` per ON per.parent = pe.name
        INNER JOIN `tabJournal Entry` je ON per.reference_name = je.name
        WHERE pe.party_type = 'Supplier'
        AND pe.party = %s
        AND pe.docstatus = 1
        AND pe.reference_date BETWEEN %s AND %s
        AND per.reference_doctype = 'Journal Entry'
        AND (je.user_remark LIKE %s OR je.user_remark LIKE %s)
        ORDER BY pe.reference_date DESC
    """, (linked_supplier, from_date, to_date,
          f"%Commission%{sales_partner}%",
          f"%commission%{sales_partner}%"), as_dict=True)
    
    # Combine all payments
    all_payments = direct_payments + journal_referenced_payments
    
    # Sort by reference date (most recent first)
    all_payments.sort(key=lambda x: x.reference_date, reverse=True)
    
    return all_payments

def get_sales_partner_commission_rate(sales_partner):
    """
    Get commission rate for DLITS sales partner
    """
    commission_rate = frappe.db.get_value("DLITS Sales Partner", sales_partner, "commission_rate")
    return flt(commission_rate or 0)

@frappe.whitelist()
def create_bulk_commission_payments(sales_partners_data):
    """
    Create bulk commission payments for multiple sales partners
    sales_partners_data: JSON string with list of {sales_partner, amount, reference_date}
    """
    import json
    
    if isinstance(sales_partners_data, str):
        sales_partners_data = json.loads(sales_partners_data)
    
    created_payments = []
    errors = []
    
    for data in sales_partners_data:
        try:
            sales_partner = data.get('sales_partner')
            amount = flt(data.get('amount', 0))
            reference_date = data.get('reference_date', today())
            
            if amount <= 0:
                errors.append(f"Invalid amount for {sales_partner}")
                continue
            
            # Get linked supplier
            linked_supplier = frappe.db.get_value("Supplier", {"sales_partner_link": sales_partner}, "name")
            
            if not linked_supplier:
                errors.append(f"No linked supplier found for {sales_partner}")
                continue
            
            # Create payment entry
            payment_entry = frappe.get_doc({
                "doctype": "Payment Entry",
                "payment_type": "Pay",
                "party_type": "Supplier",
                "party": linked_supplier,
                "paid_amount": amount,
                "received_amount": amount,
                "reference_date": reference_date,
                "remarks": f"Commission payment for Sales Partner: {sales_partner}",
                "mode_of_payment": frappe.db.get_single_value("Accounts Settings", "default_payment_mode_of_payment") or "Cash"
            })
            
            payment_entry.insert()
            created_payments.append({
                "sales_partner": sales_partner,
                "payment_entry": payment_entry.name,
                "amount": amount
            })
            
        except Exception as e:
            errors.append(f"Error creating payment for {sales_partner}: {str(e)}")
    
    return {
        "created_payments": created_payments,
        "errors": errors
    }

@frappe.whitelist()
def get_outstanding_commissions(from_date=None, to_date=None):
    """
    Get all sales partners with outstanding commissions
    """
    if not from_date:
        from_date = frappe.utils.add_months(today(), -3)  # Last 3 months
    if not to_date:
        to_date = today()
    
    # Get all active DLITS sales partners
    sales_partners = frappe.db.sql("""
        SELECT name, partner_name, commission_rate
        FROM `tabDLITS Sales Partner`
        WHERE status = 'Active'
    """, as_dict=True)
    
    outstanding_data = []
    
    for sp in sales_partners:
        summary = get_sales_partner_commission_summary(sp.name, from_date, to_date)
        
        # Get the actual outstanding commission from DLITS Sales Partner record
        partner_record = frappe.get_doc("DLITS Sales Partner", sp.name)
        actual_outstanding = flt(partner_record.outstanding_commission or 0)
        actual_total_commission = flt(partner_record.total_commission_earned or 0)
        actual_paid_commission = flt(partner_record.total_commission_paid or 0)
        actual_total_sales = flt(partner_record.total_sales or 0)
        
        # Use the higher values between calculated and stored
        final_total_commission = max(summary['total_commission'], actual_total_commission)
        final_paid_commission = max(summary['paid_commission'], actual_paid_commission)
        final_outstanding_commission = max(summary['outstanding_commission'], actual_outstanding)
        final_total_sales = max(summary['total_sales'], actual_total_sales)
        
        if final_outstanding_commission > 0:
            # Get supplier name if linked_supplier_id exists
            supplier_display = summary.get('linked_supplier', 'Not Linked')
            if summary.get('linked_supplier_id'):
                supplier_name = frappe.db.get_value("Supplier", summary['linked_supplier_id'], "supplier_name")
                supplier_display = supplier_name or summary['linked_supplier_id']
            
            outstanding_data.append({
                "sales_partner": sp.name,
                "partner_name": sp.partner_name,
                "commission_rate": sp.commission_rate,
                "total_commission": final_total_commission,
                "paid_commission": final_paid_commission,
                "outstanding_commission": final_outstanding_commission,
                "total_orders": summary['total_orders'],
                "total_sales": final_total_sales,
                "linked_supplier": supplier_display
            })
    
    # Sort by outstanding commission (highest first)
    outstanding_data.sort(key=lambda x: x['outstanding_commission'], reverse=True)
    
    return outstanding_data

@frappe.whitelist()
def debug_commission_calculation(sales_partner, from_date=None, to_date=None):
    """
    Debug method to show detailed commission calculation breakdown
    """
    if not from_date:
        from_date = frappe.utils.add_months(today(), -3)
    if not to_date:
        to_date = today()
    
    linked_supplier = frappe.db.get_value("Supplier", {"sales_partner_link": sales_partner}, "name")
    
    debug_info = {
        "sales_partner": sales_partner,
        "linked_supplier": linked_supplier,
        "from_date": from_date,
        "to_date": to_date,
        "commission_sources": {},
        "payment_sources": {},
        "summary": {}
    }
    
    # Get commission sources
    so_commission = frappe.db.sql("""
        SELECT
            SUM(dlits_commission_amount) as total_commission,
            COUNT(*) as order_count,
            SUM(base_grand_total) as total_sales
        FROM `tabSales Order`
        WHERE dlits_sales_partner = %s
        AND docstatus = 1
        AND transaction_date BETWEEN %s AND %s
    """, (sales_partner, from_date, to_date), as_dict=True)
    
    si_commission = frappe.db.sql("""
        SELECT
            SUM(dlits_commission_amount) as total_commission,
            COUNT(*) as invoice_count,
            SUM(base_grand_total) as total_sales
        FROM `tabSales Invoice`
        WHERE dlits_sales_partner = %s
        AND docstatus = 1
        AND posting_date BETWEEN %s AND %s
    """, (sales_partner, from_date, to_date), as_dict=True)
    
    debug_info["commission_sources"] = {
        "sales_orders": so_commission[0] if so_commission else {},
        "sales_invoices": si_commission[0] if si_commission else {}
    }
    
    if linked_supplier:
        # Method 1: Direct payments
        direct_payments = frappe.db.sql("""
            SELECT name, reference_date, paid_amount, remarks
            FROM `tabPayment Entry`
            WHERE party_type = 'Supplier'
            AND party = %s
            AND docstatus = 1
            AND reference_date BETWEEN %s AND %s
            AND (remarks LIKE %s OR remarks LIKE %s)
        """, (linked_supplier, from_date, to_date,
              f"%Commission payment for Sales Partner: {sales_partner}%",
              f"%Commission%{sales_partner}%"), as_dict=True)
        
        # Method 2: Journal Entry payments
        journal_payments = frappe.db.sql("""
            SELECT
                pe.name as payment_entry,
                pe.reference_date,
                per.allocated_amount,
                per.reference_name as journal_entry,
                je.user_remark
            FROM `tabPayment Entry Reference` per
            INNER JOIN `tabPayment Entry` pe ON per.parent = pe.name
            INNER JOIN `tabJournal Entry` je ON per.reference_name = je.name
            WHERE pe.party_type = 'Supplier'
            AND pe.party = %s
            AND pe.docstatus = 1
            AND pe.reference_date BETWEEN %s AND %s
            AND per.reference_doctype = 'Journal Entry'
            AND (je.user_remark LIKE %s OR je.user_remark LIKE %s)
        """, (linked_supplier, from_date, to_date,
              f"%Commission%{sales_partner}%",
              f"%commission%{sales_partner}%"), as_dict=True)
        
        # Method 3: All Journal Entries for this sales partner
        all_journal_entries = frappe.db.sql("""
            SELECT
                je.name,
                je.posting_date,
                je.total_debit,
                je.user_remark,
                COALESCE(SUM(per.allocated_amount), 0) as allocated_amount
            FROM `tabJournal Entry` je
            LEFT JOIN `tabPayment Entry Reference` per ON per.reference_name = je.name
                AND per.reference_doctype = 'Journal Entry'
            LEFT JOIN `tabPayment Entry` pe ON per.parent = pe.name AND pe.docstatus = 1
            WHERE je.docstatus = 1
            AND je.posting_date BETWEEN %s AND %s
            AND (je.user_remark LIKE %s OR je.user_remark LIKE %s)
            GROUP BY je.name, je.posting_date, je.total_debit, je.user_remark
        """, (from_date, to_date,
              f"%Commission%{sales_partner}%",
              f"%commission%{sales_partner}%"), as_dict=True)
        
        debug_info["payment_sources"] = {
            "direct_payments": direct_payments,
            "journal_payments": journal_payments,
            "all_journal_entries": all_journal_entries
        }
    
    # Calculate summary using the actual function
    summary = get_sales_partner_commission_summary(sales_partner, from_date, to_date)
    debug_info["summary"] = summary
    
    return debug_info