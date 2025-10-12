import frappe
from frappe import _
from frappe.utils import flt, getdate, today

@frappe.whitelist()
def get_dlits_sales_partner_commission_summary(sales_partner, from_date=None, to_date=None):
    """
    Get commission summary for a DLITS Sales Partner
    """
    if not from_date:
        from_date = frappe.utils.add_months(today(), -1)
    if not to_date:
        to_date = today()
    
    # Get commission from Sales Orders
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
    
    # Get commission from Sales Invoices
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
    
    # Get paid commission from DLITS Sales Partner record
    partner_doc = frappe.get_doc("DLITS Sales Partner", sales_partner)
    paid_commission = flt(partner_doc.total_commission_paid or 0)
    
    # Calculate totals
    total_commission = flt(so_commission[0].total_commission or 0) + flt(si_commission[0].total_commission or 0)
    total_orders = (so_commission[0].order_count or 0) + (si_commission[0].invoice_count or 0)
    total_sales = flt(so_commission[0].total_sales or 0) + flt(si_commission[0].total_sales or 0)
    outstanding_commission = total_commission - paid_commission
    
    return {
        "sales_partner": sales_partner,
        "from_date": from_date,
        "to_date": to_date,
        "total_commission": total_commission,
        "paid_commission": paid_commission,
        "outstanding_commission": outstanding_commission,
        "total_orders": total_orders,
        "total_sales": total_sales,
        "linked_supplier": partner_doc.supplier,
        "commission_rate": partner_doc.commission_rate,
        "commission_type": partner_doc.commission_type
    }

@frappe.whitelist()
def get_dlits_sales_partner_commission_details(sales_partner, from_date=None, to_date=None):
    """
    Get detailed commission breakdown for a DLITS Sales Partner
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
            dlits_commission_amount as commission_amount,
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
            dlits_commission_amount as commission_amount,
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
def get_dlits_sales_partner_payment_history(sales_partner, from_date=None, to_date=None):
    """
    Get payment history for a DLITS Sales Partner
    """
    if not from_date:
        from_date = frappe.utils.add_months(today(), -12)  # Last 12 months
    if not to_date:
        to_date = today()
    
    # Get DLITS Sales Partner
    partner_doc = frappe.get_doc("DLITS Sales Partner", sales_partner)
    
    if not partner_doc.supplier:
        return []
    
    # Get payment entries for the linked supplier
    payments = frappe.db.sql("""
        SELECT
            name,
            reference_date,
            paid_amount,
            remarks,
            mode_of_payment,
            reference_no,
            'Commission Payment' as payment_type
        FROM `tabPayment Entry`
        WHERE party_type = 'Supplier'
        AND party = %s
        AND docstatus = 1
        AND reference_date BETWEEN %s AND %s
        AND (remarks LIKE %s OR reference_no LIKE %s)
        ORDER BY reference_date DESC
    """, (partner_doc.supplier, from_date, to_date,
          f"%{sales_partner}%", f"%Commission%"), as_dict=True)
    
    return payments

@frappe.whitelist()
def get_dlits_commission_rate(sales_partner):
    """
    Get commission rate for DLITS Sales Partner
    """
    if not sales_partner:
        return {"commission_type": "Percentage", "commission_rate": 0}
    
    partner = frappe.get_doc("DLITS Sales Partner", sales_partner)
    return {
        "commission_type": partner.commission_type,
        "commission_rate": partner.commission_rate,
        "minimum_commission": partner.minimum_commission,
        "maximum_commission": partner.maximum_commission
    }

@frappe.whitelist()
def create_bulk_dlits_commission_payments(sales_partners_data):
    """
    Create bulk commission payments for multiple DLITS Sales Partners
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
            
            # Use the DLITS Sales Partner payment method
            from dlitscustom.dlitscustom.doctype.dlits_sales_partner.dlits_sales_partner import create_commission_payment
            
            result = create_commission_payment(sales_partner, amount, f"Bulk payment - {reference_date}")
            
            if result.get('payment_entry'):
                created_payments.append({
                    "sales_partner": sales_partner,
                    "payment_entry": result['payment_entry'].name,
                    "amount": amount
                })
            else:
                errors.append(f"Failed to create payment for {sales_partner}")
            
        except Exception as e:
            errors.append(f"Error creating payment for {sales_partner}: {str(e)}")
    
    return {
        "created_payments": created_payments,
        "errors": errors
    }

@frappe.whitelist()
def get_outstanding_dlits_commissions(from_date=None, to_date=None):
    """
    Get all DLITS Sales Partners with outstanding commissions
    """
    if not from_date:
        from_date = frappe.utils.add_months(today(), -3)  # Last 3 months
    if not to_date:
        to_date = today()
    
    # Get all active DLITS Sales Partners
    sales_partners = frappe.db.sql("""
        SELECT name, partner_name, commission_rate, outstanding_commission
        FROM `tabDLITS Sales Partner`
        WHERE status = 'Active'
        AND outstanding_commission > 0
        ORDER BY outstanding_commission DESC
    """, as_dict=True)
    
    outstanding_data = []
    
    for sp in sales_partners:
        summary = get_dlits_sales_partner_commission_summary(sp.name, from_date, to_date)
        
        if summary['outstanding_commission'] > 0:
            outstanding_data.append({
                "sales_partner": sp.name,
                "partner_name": sp.partner_name,
                "commission_rate": sp.commission_rate,
                "total_commission": summary['total_commission'],
                "paid_commission": summary['paid_commission'],
                "outstanding_commission": summary['outstanding_commission'],
                "total_orders": summary['total_orders'],
                "total_sales": summary['total_sales'],
                "linked_supplier": summary['linked_supplier']
            })
    
    return outstanding_data

@frappe.whitelist()
def update_all_dlits_partner_totals():
    """
    Update commission totals for all DLITS Sales Partners
    """
    try:
        partners = frappe.db.sql("""
            SELECT name FROM `tabDLITS Sales Partner`
            WHERE status = 'Active'
        """, as_dict=True)
        
        updated_count = 0
        errors = []
        
        for partner in partners:
            try:
                from dlitscustom.dlitscustom.doctype.dlits_sales_partner.dlits_sales_partner import update_partner_totals
                update_partner_totals(partner.name)
                updated_count += 1
            except Exception as e:
                errors.append(f"Error updating {partner.name}: {str(e)}")
        
        return {
            "success": True,
            "updated_count": updated_count,
            "total_partners": len(partners),
            "errors": errors
        }
        
    except Exception as e:
        frappe.log_error(f"Error updating partner totals: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def get_dlits_commission_dashboard_data():
    """
    Get dashboard data for DLITS commission management
    """
    try:
        # Total active partners
        active_partners = frappe.db.count("DLITS Sales Partner", {"status": "Active"})
        
        # Total outstanding commission
        outstanding_total = frappe.db.sql("""
            SELECT SUM(outstanding_commission) as total
            FROM `tabDLITS Sales Partner`
            WHERE status = 'Active'
        """, as_dict=True)[0].total or 0
        
        # This month's commission
        this_month_commission = frappe.db.sql("""
            SELECT SUM(dlits_commission_amount) as total
            FROM `tabSales Invoice`
            WHERE dlits_sales_partner IS NOT NULL
            AND docstatus = 1
            AND MONTH(posting_date) = MONTH(CURDATE())
            AND YEAR(posting_date) = YEAR(CURDATE())
        """, as_dict=True)[0].total or 0
        
        # This month's payments
        this_month_payments = frappe.db.sql("""
            SELECT COUNT(*) as count, SUM(paid_amount) as total
            FROM `tabPayment Entry`
            WHERE docstatus = 1
            AND MONTH(reference_date) = MONTH(CURDATE())
            AND YEAR(reference_date) = YEAR(CURDATE())
            AND (remarks LIKE '%commission%' OR reference_no LIKE '%Commission%')
        """, as_dict=True)[0]
        
        # Top partners by outstanding commission
        top_partners = frappe.db.sql("""
            SELECT partner_name, outstanding_commission
            FROM `tabDLITS Sales Partner`
            WHERE status = 'Active'
            AND outstanding_commission > 0
            ORDER BY outstanding_commission DESC
            LIMIT 5
        """, as_dict=True)
        
        return {
            "active_partners": active_partners,
            "outstanding_total": outstanding_total,
            "this_month_commission": this_month_commission,
            "this_month_payments": {
                "count": this_month_payments.count or 0,
                "total": this_month_payments.total or 0
            },
            "top_partners": top_partners
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting dashboard data: {str(e)}")
        return {"error": str(e)}

@frappe.whitelist()
def calculate_dlits_commission_for_transaction(doctype, docname):
    """
    Calculate commission for a specific Sales Order or Sales Invoice
    """
    try:
        doc = frappe.get_doc(doctype, docname)
        
        if not doc.dlits_sales_partner:
            return {"commission_amount": 0, "message": "No DLITS Sales Partner assigned"}
        
        partner = frappe.get_doc("DLITS Sales Partner", doc.dlits_sales_partner)
        commission_amount = partner.calculate_commission_for_amount(doc.base_grand_total)
        
        return {
            "commission_amount": commission_amount,
            "commission_type": partner.commission_type,
            "commission_rate": partner.commission_rate,
            "base_amount": doc.base_grand_total
        }
        
    except Exception as e:
        frappe.log_error(f"Error calculating commission for {doctype} {docname}: {str(e)}")
        return {"error": str(e)}

@frappe.whitelist()
def sync_dlits_commission_fields():
    """
    Sync commission fields in Sales Orders and Sales Invoices
    """
    try:
        # Update Sales Orders
        so_updated = frappe.db.sql("""
            UPDATE `tabSales Order` so
            INNER JOIN `tabDLITS Sales Partner` dsp ON so.dlits_sales_partner = dsp.name
            SET 
                so.dlits_commission_type = dsp.commission_type,
                so.dlits_commission_rate = dsp.commission_rate
            WHERE so.dlits_sales_partner IS NOT NULL
            AND so.docstatus = 1
        """)
        
        # Update Sales Invoices
        si_updated = frappe.db.sql("""
            UPDATE `tabSales Invoice` si
            INNER JOIN `tabDLITS Sales Partner` dsp ON si.dlits_sales_partner = dsp.name
            SET 
                si.dlits_commission_type = dsp.commission_type,
                si.dlits_commission_rate = dsp.commission_rate
            WHERE si.dlits_sales_partner IS NOT NULL
            AND si.docstatus = 1
        """)
        
        frappe.db.commit()
        
        return {
            "success": True,
            "sales_orders_updated": so_updated,
            "sales_invoices_updated": si_updated
        }
        
    except Exception as e:
        frappe.log_error(f"Error syncing commission fields: {str(e)}")
        return {"success": False, "error": str(e)}