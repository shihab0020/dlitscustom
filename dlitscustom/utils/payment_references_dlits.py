import frappe
from frappe import _
from frappe.utils import flt, getdate

@frappe.whitelist()
def get_outstanding_commission_references(sales_partner, from_date=None, to_date=None):
    """
    Get outstanding commission references for Payment Entry
    This will look for existing Journal Entries for commission accruals
    """
    if not from_date:
        from_date = frappe.utils.add_months(frappe.utils.today(), -3)
    if not to_date:
        to_date = frappe.utils.today()
    
    references = []
    
    # Get linked supplier
    linked_supplier = frappe.db.get_value("DLITS Sales Partner", sales_partner, "supplier")
    
    if not linked_supplier:
        return references
    
    # Look for existing Journal Entries with outstanding amounts for this supplier
    journal_entries = frappe.db.sql("""
        SELECT DISTINCT
            je.name,
            je.posting_date,
            je.total_debit as total_amount,
            (je.total_debit - COALESCE(pe_ref.allocated_sum, 0)) as outstanding_amount
        FROM `tabJournal Entry` je
        LEFT JOIN (
            SELECT
                reference_name,
                SUM(allocated_amount) as allocated_sum
            FROM `tabPayment Entry Reference`
            WHERE reference_doctype = 'Journal Entry'
            AND docstatus = 1
            GROUP BY reference_name
        ) pe_ref ON pe_ref.reference_name = je.name
        WHERE je.docstatus = 1
        AND je.posting_date BETWEEN %s AND %s
        AND je.user_remark LIKE %s
        AND (je.total_debit - COALESCE(pe_ref.allocated_sum, 0)) > 0
        ORDER BY je.posting_date DESC
    """, (from_date, to_date, f"%Commission%{sales_partner}%"), as_dict=True)
    
    for je in journal_entries:
        references.append({
            "reference_doctype": "Journal Entry",
            "reference_name": je.name,
            "due_date": je.posting_date,
            "total_amount": flt(je.total_amount),
            "outstanding_amount": flt(je.outstanding_amount),
            "allocated_amount": flt(je.outstanding_amount)
        })
    
    return references

@frappe.whitelist()
def create_commission_journal_entries(sales_partner, commission_amount, reference_date=None):
    """
    Create Journal Entry for commission payment if needed
    This creates proper accounting entries for commission payments
    """
    try:
        if not reference_date:
            reference_date = frappe.utils.today()
        
        # Get linked supplier
        linked_supplier = frappe.db.get_value("DLITS Sales Partner", sales_partner, "supplier")
        
        if not linked_supplier:
            frappe.throw(_("No linked supplier found for Sales Partner {0}").format(sales_partner))
        
        # Get default accounts
        company = frappe.defaults.get_user_default("Company")
        commission_expense_account = frappe.db.get_value("Company", company, "default_expense_account")
        payable_account = frappe.db.get_value("Supplier", linked_supplier, "default_payable_account")
        
        if not payable_account:
            payable_account = frappe.db.get_value("Company", company, "default_payable_account")
        
        # Create Journal Entry
        journal_entry = frappe.get_doc({
            "doctype": "Journal Entry",
            "voucher_type": "Journal Entry",
            "company": company,
            "posting_date": reference_date,
            "user_remark": f"Commission accrual for Sales Partner: {sales_partner}",
            "accounts": [
                {
                    "account": commission_expense_account,
                    "debit_in_account_currency": commission_amount,
                    "credit_in_account_currency": 0,
                    "user_remark": f"Commission expense for {sales_partner}"
                },
                {
                    "account": payable_account,
                    "party_type": "Supplier",
                    "party": linked_supplier,
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": commission_amount,
                    "user_remark": f"Commission payable to {linked_supplier}"
                }
            ]
        })
        
        journal_entry.insert()
        journal_entry.submit()
        
        return {
            "journal_entry": journal_entry.name,
            "reference_doctype": "Journal Entry",
            "reference_name": journal_entry.name,
            "total_amount": commission_amount,
            "outstanding_amount": commission_amount,
            "allocated_amount": commission_amount
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating commission journal entry: {str(e)}")
        frappe.throw(_("Error creating commission journal entry: {0}").format(str(e)))

@frappe.whitelist()
def get_payment_references_for_commission(sales_partner, commission_amount, from_date=None, to_date=None):
    """
    Get or create payment references for commission payment
    This is the main function called by the frontend
    """
    try:
        # First try to get existing outstanding references
        references = get_outstanding_commission_references(sales_partner, from_date, to_date)
        
        # If no outstanding references found, create journal entries for outstanding commissions
        if not references:
            # Get commission details to create individual journal entries
            commission_details = get_commission_details_for_accrual(sales_partner, from_date, to_date)
            
            if commission_details:
                # Create journal entries for each commission transaction
                for detail in commission_details:
                    journal_ref = create_commission_journal_entry_for_transaction(
                        sales_partner,
                        detail['amount'],
                        detail['reference_doc'],
                        detail['reference_name'],
                        detail['posting_date']
                    )
                    if journal_ref:
                        references.append(journal_ref)
            else:
                # Fallback: create single journal entry for total commission
                journal_ref = create_commission_journal_entries(sales_partner, commission_amount)
                references = [journal_ref]
        
        # Ensure total allocated amount matches commission amount
        total_allocated = sum(flt(ref.get("allocated_amount", 0)) for ref in references)
        
        if total_allocated != flt(commission_amount):
            # Adjust allocation proportionally
            if total_allocated > 0:
                for ref in references:
                    ref["allocated_amount"] = flt(ref["allocated_amount"]) * flt(commission_amount) / total_allocated
        
        return references
        
    except Exception as e:
        frappe.log_error(f"Error getting payment references: {str(e)}")
        return []

@frappe.whitelist()
def get_commission_details_for_accrual(sales_partner, from_date=None, to_date=None):
    """
    Get commission details from Sales Orders and Invoices for creating accrual entries
    """
    if not from_date:
        from_date = frappe.utils.add_months(frappe.utils.today(), -3)
    if not to_date:
        to_date = frappe.utils.today()
    
    commission_details = []
    
    # Get Sales Orders with commission
    sales_orders = frappe.db.sql("""
        SELECT
            name,
            transaction_date as posting_date,
            total_commission
        FROM `tabSales Order`
        WHERE sales_partner = %s
        AND docstatus = 1
        AND transaction_date BETWEEN %s AND %s
        AND total_commission > 0
        ORDER BY transaction_date DESC
    """, (sales_partner, from_date, to_date), as_dict=True)
    
    for so in sales_orders:
        commission_details.append({
            "reference_doc": "Sales Order",
            "reference_name": so.name,
            "posting_date": so.posting_date,
            "amount": flt(so.total_commission)
        })
    
    # Get Sales Invoices with commission
    sales_invoices = frappe.db.sql("""
        SELECT
            name,
            posting_date,
            total_commission
        FROM `tabSales Invoice`
        WHERE sales_partner = %s
        AND docstatus = 1
        AND posting_date BETWEEN %s AND %s
        AND total_commission > 0
        ORDER BY posting_date DESC
    """, (sales_partner, from_date, to_date), as_dict=True)
    
    for si in sales_invoices:
        commission_details.append({
            "reference_doc": "Sales Invoice",
            "reference_name": si.name,
            "posting_date": si.posting_date,
            "amount": flt(si.total_commission)
        })
    
    return commission_details

def create_commission_journal_entry_for_transaction(sales_partner, commission_amount, reference_doc, reference_name, posting_date):
    """
    Create Journal Entry for a specific commission transaction
    """
    try:
        # Get linked supplier
        linked_supplier = frappe.db.get_value("DLITS Sales Partner", sales_partner, "supplier")
        
        if not linked_supplier:
            frappe.throw(_("No linked supplier found for Sales Partner {0}").format(sales_partner))
        
        # Check if Journal Entry already exists for this transaction
        existing_je = frappe.db.exists("Journal Entry", {
            "user_remark": ["like", f"%{reference_name}%Commission%{sales_partner}%"],
            "docstatus": 1
        })
        
        if existing_je:
            # Return existing journal entry as reference
            je_doc = frappe.get_doc("Journal Entry", existing_je)
            return {
                "reference_doctype": "Journal Entry",
                "reference_name": je_doc.name,
                "due_date": je_doc.posting_date,
                "total_amount": commission_amount,
                "outstanding_amount": commission_amount,
                "allocated_amount": commission_amount
            }
        
        # Get default accounts
        company = frappe.defaults.get_user_default("Company")
        commission_expense_account = frappe.db.get_value("Company", company, "default_expense_account")
        payable_account = frappe.db.get_value("Supplier", linked_supplier, "default_payable_account")
        
        if not payable_account:
            payable_account = frappe.db.get_value("Company", company, "default_payable_account")
        
        # Create Journal Entry
        journal_entry = frappe.get_doc({
            "doctype": "Journal Entry",
            "voucher_type": "Journal Entry",
            "company": company,
            "posting_date": posting_date,
            "user_remark": f"Commission accrual for {reference_doc} {reference_name} - Sales Partner: {sales_partner}",
            "accounts": [
                {
                    "account": commission_expense_account,
                    "debit_in_account_currency": commission_amount,
                    "credit_in_account_currency": 0,
                    "user_remark": f"Commission expense for {reference_name}"
                },
                {
                    "account": payable_account,
                    "party_type": "Supplier",
                    "party": linked_supplier,
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": commission_amount,
                    "user_remark": f"Commission payable to {linked_supplier}"
                }
            ]
        })
        
        journal_entry.insert()
        journal_entry.submit()
        
        return {
            "reference_doctype": "Journal Entry",
            "reference_name": journal_entry.name,
            "due_date": journal_entry.posting_date,
            "total_amount": commission_amount,
            "outstanding_amount": commission_amount,
            "allocated_amount": commission_amount
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating commission journal entry for {reference_name}: {str(e)}")
        return None

@frappe.whitelist()
def get_default_commission_accounts(company, supplier):
    """
    Get default accounts for commission journal entries
    """
    try:
        frappe.logger().info(f"Getting default accounts for company: {company}, supplier: {supplier}")
        
        accounts = {}
        
        # Validate inputs
        if not company:
            company = frappe.defaults.get_user_default("Company")
        if not company:
            frappe.throw("Company is required")
        
        if not supplier:
            frappe.throw("Supplier is required")
        
        # Check if supplier exists
        if not frappe.db.exists("Supplier", supplier):
            frappe.throw(f"Supplier {supplier} does not exist")
        
        # Get expense account - try multiple approaches
        expense_account = None
        
        # 1. Try company default expense account
        expense_account = frappe.db.get_value("Company", company, "default_expense_account")
        frappe.logger().info(f"Company default expense account: {expense_account}")
        
        # 2. Try to find commission-specific expense account
        if not expense_account:
            expense_account = frappe.db.sql("""
                SELECT name FROM `tabAccount`
                WHERE company = %s
                AND account_type = 'Expense Account'
                AND is_group = 0
                AND (account_name LIKE '%commission%' OR account_name LIKE '%Commission%')
                LIMIT 1
            """, (company,))
            if expense_account:
                expense_account = expense_account[0][0]
                frappe.logger().info(f"Found commission expense account: {expense_account}")
        
        # 3. Fallback to any expense account
        if not expense_account:
            expense_account = frappe.db.sql("""
                SELECT name FROM `tabAccount`
                WHERE company = %s
                AND account_type = 'Expense Account'
                AND is_group = 0
                LIMIT 1
            """, (company,))
            if expense_account:
                expense_account = expense_account[0][0]
                frappe.logger().info(f"Fallback expense account: {expense_account}")
        
        accounts["expense_account"] = expense_account
        
        # Get payable account - try multiple approaches
        payable_account = None
        
        # 1. Try supplier's default payable account
        supplier_doc = frappe.get_doc("Supplier", supplier)
        if hasattr(supplier_doc, 'accounts'):
            for acc in supplier_doc.accounts:
                if acc.company == company:
                    payable_account = acc.account
                    break
        
        frappe.logger().info(f"Supplier default payable account: {payable_account}")
        
        # 2. Try company default payable account
        if not payable_account:
            payable_account = frappe.db.get_value("Company", company, "default_payable_account")
            frappe.logger().info(f"Company default payable account: {payable_account}")
        
        # 3. Fallback to any payable account
        if not payable_account:
            payable_account = frappe.db.sql("""
                SELECT name FROM `tabAccount`
                WHERE company = %s
                AND account_type = 'Payable'
                AND is_group = 0
                LIMIT 1
            """, (company,))
            if payable_account:
                payable_account = payable_account[0][0]
                frappe.logger().info(f"Fallback payable account: {payable_account}")
        
        accounts["payable_account"] = payable_account
        
        frappe.logger().info(f"Final accounts: {accounts}")
        return accounts
        
    except Exception as e:
        error_msg = f"Error getting default commission accounts: {str(e)}"
        frappe.logger().error(error_msg)
        frappe.log_error(error_msg)
        return {
            "expense_account": None,
            "payable_account": None,
            "error": str(e)
        }

@frappe.whitelist()
def test_account_lookup():
    """
    Test method to verify account lookup functionality
    """
    try:
        # Get default company
        company = frappe.defaults.get_user_default("Company")
        if not company:
            company = frappe.db.get_single_value("Global Defaults", "default_company")
        
        # Get any supplier for testing
        supplier = frappe.db.get_value("Supplier", {}, "name")
        
        if not company:
            return {"error": "No company found"}
        
        if not supplier:
            return {"error": "No supplier found"}
        
        # Test the account lookup
        result = get_default_commission_accounts(company, supplier)
        
        return {
            "company": company,
            "supplier": supplier,
            "accounts": result,
            "success": True
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }