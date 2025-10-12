# Copyright (c) 2024, DLITS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate, add_days

class DLITSSalesPartner(Document):
    def validate(self):
        """Validate DLITS Sales Partner data"""
        self.validate_commission_rate()
        self.validate_dates()
        self.validate_bank_details()
        self.calculate_outstanding_commission()
    
    def before_save(self):
        """Before save operations"""
        if not self.partner_code:
            self.partner_code = self.generate_partner_code()
        
        if not self.start_date:
            self.start_date = nowdate()
    
    def after_insert(self):
        """After insert operations - placeholder method"""
        # This method is required by the system but currently does nothing
        # Future functionality like auto-creating suppliers can be added here
        pass
    
    def validate_commission_rate(self):
        """Validate commission rate based on type"""
        if self.commission_type == "Percentage":
            if flt(self.commission_rate) <= 0 or flt(self.commission_rate) > 100:
                frappe.throw("Commission rate must be between 0.01% and 100%")
        elif self.commission_type == "Fixed Amount":
            if flt(self.commission_rate) <= 0:
                frappe.throw("Fixed commission amount must be greater than 0")
    
    def validate_dates(self):
        """Validate date fields"""
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                frappe.throw("Partnership end date must be after start date")
    
    def validate_bank_details(self):
        """Validate bank details if provided"""
        if self.iban and len(self.iban) < 15:
            frappe.throw("IBAN must be at least 15 characters long")
        
        if self.swift_code and len(self.swift_code) not in [8, 11]:
            frappe.throw("SWIFT code must be 8 or 11 characters long")
    
    def generate_partner_code(self):
        """Generate unique partner code"""
        # Get first 3 letters of partner name
        name_part = ''.join([c for c in self.partner_name if c.isalpha()])[:3].upper()
        
        # Get next number in sequence
        existing_codes = frappe.db.sql("""
            SELECT partner_code FROM `tabDLITS Sales Partner` 
            WHERE partner_code LIKE %s 
            ORDER BY partner_code DESC LIMIT 1
        """, (f"{name_part}%",))
        
        if existing_codes:
            last_code = existing_codes[0][0]
            try:
                last_num = int(last_code[3:])
                new_num = last_num + 1
            except:
                new_num = 1
        else:
            new_num = 1
        
        return f"{name_part}{new_num:04d}"
    
    def create_supplier(self):
        """Create linked supplier for commission payments"""
        if self.supplier:
            return  # Supplier already exists
        
        try:
            supplier = frappe.get_doc({
                "doctype": "Supplier",
                "supplier_name": f"{self.partner_name} (Sales Partner)",
                "supplier_group": self.get_or_create_supplier_group(),
                "supplier_type": "Company" if self.partner_type == "Company" else "Individual",
                "country": self.country,
                "is_frozen": 0
            })
            
            supplier.insert(ignore_permissions=True)
            
            # Link the supplier back to this sales partner
            self.db_set("supplier", supplier.name)
            
            frappe.msgprint(f"Supplier '{supplier.name}' created and linked successfully")
            
        except Exception as e:
            frappe.log_error(f"Error creating supplier for {self.name}: {str(e)}")
            frappe.throw(f"Failed to create supplier: {str(e)}")
    
    def get_or_create_supplier_group(self):
        """Get or create supplier group for sales partners"""
        group_name = "Sales Partners"
        
        if not frappe.db.exists("Supplier Group", group_name):
            supplier_group = frappe.get_doc({
                "doctype": "Supplier Group",
                "supplier_group_name": group_name,
                "parent_supplier_group": frappe.db.get_single_value("Buying Settings", "supplier_group") or "All Supplier Groups"
            })
            supplier_group.insert(ignore_permissions=True)
        
        return group_name
    
    def calculate_outstanding_commission(self):
        """Calculate outstanding commission"""
        self.outstanding_commission = flt(self.total_commission_earned) - flt(self.total_commission_paid)
    
    def update_commission_totals(self):
        """Update commission totals from sales transactions"""
        # Get total sales and commission from Sales Invoices ONLY (not Sales Orders to avoid double counting)
        sales_data = frappe.db.sql("""
            SELECT
                COALESCE(SUM(grand_total), 0) as total_sales,
                COALESCE(SUM(dlits_commission_amount), 0) as total_commission
            FROM `tabSales Invoice`
            WHERE dlits_sales_partner = %s
            AND docstatus = 1
        """, (self.name,), as_dict=True)
        
        if sales_data:
            self.db_set("total_sales", sales_data[0].total_sales)
            self.db_set("total_commission_earned", sales_data[0].total_commission)
        
        # Get total commission paid from Payment Entries (avoid double counting with single comprehensive query)
        paid_commission = 0
        
        # Use a single comprehensive query to avoid double counting
        if self.supplier:
            # Get all payments to linked supplier with commission references
            supplier_payments = frappe.db.sql("""
                SELECT DISTINCT pe.name, pe.paid_amount
                FROM `tabPayment Entry` pe
                WHERE pe.party_type = 'Supplier'
                AND pe.party = %s
                AND pe.docstatus = 1
                AND (pe.remarks LIKE %s OR pe.remarks LIKE %s OR pe.reference_no LIKE %s)
            """, (self.supplier,
                  f"%Commission payment for Sales Partner: {self.partner_name}%",
                  f"%Commission%{self.name}%",
                  f"%Commission-{self.name}%"), as_dict=True)
            
            # Sum up the distinct payments
            for payment in supplier_payments:
                paid_commission += flt(payment.paid_amount)
        
        else:
            # Fallback: Check payments directly to sales partner (when no supplier linked)
            direct_partner_payments = frappe.db.sql("""
                SELECT DISTINCT pe.name, pe.paid_amount
                FROM `tabPayment Entry` pe
                WHERE pe.docstatus = 1
                AND (pe.party = %s OR pe.remarks LIKE %s OR pe.reference_no LIKE %s)
            """, (f"{self.name} (Sales Partner)",
                  f"%Commission%{self.name}%",
                  f"%Commission-{self.name}%"), as_dict=True)
            
            # Sum up the distinct payments
            for payment in direct_partner_payments:
                paid_commission += flt(payment.paid_amount)
        
        self.db_set("total_commission_paid", paid_commission)
        
        # Update outstanding commission
        self.calculate_outstanding_commission()
        self.db_set("outstanding_commission", self.outstanding_commission)
    
    def calculate_commission_for_amount(self, amount):
        """Calculate commission for a given amount"""
        if self.commission_type == "Percentage":
            commission = flt(amount) * flt(self.commission_rate) / 100
        else:  # Fixed Amount
            commission = flt(self.commission_rate)
        
        # Apply minimum and maximum limits
        if self.minimum_commission and commission < flt(self.minimum_commission):
            commission = flt(self.minimum_commission)
        
        if self.maximum_commission and commission > flt(self.maximum_commission):
            commission = flt(self.maximum_commission)
        
        return commission
    
    def create_commission_payment_entry(self, amount, reference_doc=None):
        """Create payment entry for commission"""
        if not self.supplier:
            frappe.throw("No supplier linked to create payment entry")
        
        payment_entry = frappe.get_doc({
            "doctype": "Payment Entry",
            "payment_type": "Pay",
            "party_type": "Supplier",
            "party": self.supplier,
            "paid_amount": amount,
            "received_amount": amount,
            "reference_no": f"Commission-{self.name}",
            "reference_date": nowdate(),
            "remarks": f"Commission payment for sales partner {self.partner_name}"
        })
        
        if reference_doc:
            payment_entry.remarks += f" - Reference: {reference_doc}"
        
        return payment_entry
    
    def get_commission_summary(self, from_date=None, to_date=None):
        """Get commission summary for a date range"""
        conditions = ["dlits_sales_partner = %s", "docstatus = 1"]
        values = [self.name]
        
        if from_date:
            conditions.append("posting_date >= %s")
            values.append(from_date)
        
        if to_date:
            conditions.append("posting_date <= %s")
            values.append(to_date)
        
        where_clause = " AND ".join(conditions)
        
        summary = frappe.db.sql(f"""
            SELECT 
                COUNT(*) as total_invoices,
                COALESCE(SUM(grand_total), 0) as total_sales,
                COALESCE(SUM(dlits_commission_amount), 0) as total_commission,
                COALESCE(SUM(CASE WHEN dlits_commission_paid_amount > 0 THEN dlits_commission_amount ELSE 0 END), 0) as paid_commission,
                COALESCE(SUM(CASE WHEN dlits_commission_paid_amount = 0 THEN dlits_commission_amount ELSE 0 END), 0) as unpaid_commission
            FROM `tabSales Invoice`
            WHERE {where_clause}
        """, values, as_dict=True)
        
        return summary[0] if summary else {}

@frappe.whitelist()
def get_commission_rate(sales_partner):
    """Get commission rate for a sales partner"""
    if not sales_partner:
        return 0
    
    partner = frappe.get_doc("DLITS Sales Partner", sales_partner)
    return {
        "commission_type": partner.commission_type,
        "commission_rate": partner.commission_rate,
        "minimum_commission": partner.minimum_commission,
        "maximum_commission": partner.maximum_commission
    }

@frappe.whitelist()
def calculate_commission(sales_partner, amount):
    """Calculate commission for a given amount"""
    if not sales_partner or not amount:
        return 0
    
    partner = frappe.get_doc("DLITS Sales Partner", sales_partner)
    return partner.calculate_commission_for_amount(flt(amount))

@frappe.whitelist()
def create_commission_payment(sales_partner, amount, reference_doc=None, paid_from_account=None, create_draft=True):
    """Create commission payment entry with proper account setup and payment references"""
    try:
        partner = frappe.get_doc("DLITS Sales Partner", sales_partner)
        
        # Ensure supplier exists
        if not partner.supplier:
            if partner.auto_create_supplier:
                partner.create_supplier()
                partner.reload()  # Reload to get the updated supplier field
            else:
                frappe.throw("No supplier linked. Please create or link a supplier first.")
        
        # Get default company
        company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
        if not company:
            company = frappe.db.get_value("Company", {}, "name")
        
        # Get default mode of payment - use a safe fallback
        default_mode_of_payment = "Cash"
        try:
            # Try to get from Mode of Payment doctype
            mode_of_payment = frappe.db.get_value("Mode of Payment", {"enabled": 1}, "name")
            if mode_of_payment:
                default_mode_of_payment = mode_of_payment
        except:
            pass
        
        # Create payment entry using frappe.get_doc for better field handling
        payment_entry = frappe.get_doc({
            "doctype": "Payment Entry",
            "payment_type": "Pay",
            "party_type": "Supplier",
            "party": partner.supplier,
            "paid_amount": flt(amount),
            "received_amount": flt(amount),
            "posting_date": nowdate(),
            "company": company,
            "reference_no": f"Commission-{partner.name}",
            "reference_date": nowdate(),
            "remarks": f"Commission payment for Sales Partner: {partner.partner_name}",
            "mode_of_payment": default_mode_of_payment
        })
        
        # Add reference if provided
        if reference_doc:
            payment_entry.remarks += f" - Reference: {reference_doc}"
        
        # Set accounts with comprehensive fallback logic
        try:
            # Get default accounts from company
            company_doc = frappe.get_doc("Company", company)
            
            # Use provided paid_from_account or get default
            if paid_from_account:
                payment_entry.paid_from = paid_from_account
            else:
                # Try company default cash account first
                if company_doc.default_cash_account:
                    payment_entry.paid_from = company_doc.default_cash_account
                else:
                    # Fallback to any cash/bank account
                    fallback_account = frappe.db.get_value("Account", {
                        "account_type": ["in", ["Cash", "Bank"]],
                        "company": company,
                        "is_group": 0
                    }, "name")
                    if fallback_account:
                        payment_entry.paid_from = fallback_account
            
            # Get paid_to account (Supplier Payable)
            paid_to_account = None
            
            # Try supplier's default payable account
            supplier_doc = frappe.get_doc("Supplier", partner.supplier)
            if hasattr(supplier_doc, 'accounts'):
                for acc in supplier_doc.accounts:
                    if acc.company == company:
                        paid_to_account = acc.account
                        break
            
            # Fallback to company default payable account
            if not paid_to_account and company_doc.default_payable_account:
                paid_to_account = company_doc.default_payable_account
            
            # Final fallback to any payable account
            if not paid_to_account:
                paid_to_account = frappe.db.get_value("Account", {
                    "account_type": "Payable",
                    "company": company,
                    "is_group": 0
                }, "name")
            
            if paid_to_account:
                payment_entry.paid_to = paid_to_account
                
        except Exception as account_error:
            frappe.log_error(f"Account mapping error: {str(account_error)}")
            # Continue - user can set accounts manually
        
        # Check for outstanding supplier invoices to reference (simplified query)
        outstanding_invoices = frappe.db.sql("""
            SELECT name, outstanding_amount, grand_total
            FROM `tabPurchase Invoice`
            WHERE supplier = %s
            AND docstatus = 1
            AND outstanding_amount > 0
            ORDER BY posting_date DESC
            LIMIT 5
        """, (partner.supplier,), as_dict=True)
        
        # Add payment references if outstanding invoices exist
        if outstanding_invoices:
            payment_entry.references = []
            remaining_amount = flt(amount)
            
            for invoice in outstanding_invoices:
                if remaining_amount <= 0:
                    break
                
                allocated_amount = min(remaining_amount, flt(invoice.outstanding_amount))
                
                payment_entry.append("references", {
                    "reference_doctype": "Purchase Invoice",
                    "reference_name": invoice.name,
                    "total_amount": flt(invoice.grand_total),
                    "outstanding_amount": flt(invoice.outstanding_amount),
                    "allocated_amount": allocated_amount
                })
                
                remaining_amount -= allocated_amount
        
        # Save payment entry as draft for user review
        payment_entry.insert(ignore_permissions=True)
        
        # Auto-submit only if create_draft is False and accounts are set
        if not create_draft and payment_entry.paid_from and payment_entry.paid_to:
            try:
                payment_entry.submit()
                status_msg = "created and submitted"
                
                # Update sales invoice commission status
                update_sales_invoice_commission_status(sales_partner, amount)
                
                # Update partner totals after successful submission
                partner.update_commission_totals()
                partner.db_set("last_commission_date", nowdate())
                
            except Exception as submit_error:
                frappe.log_error(f"Auto-submit failed: {str(submit_error)}")
                status_msg = "created as draft (auto-submit failed, please review and submit manually)"
        else:
            status_msg = "created as draft (please review accounts and submit manually)"
        
        return {
            "payment_entry": payment_entry,
            "message": f"Payment entry {payment_entry.name} {status_msg} for {frappe.format(amount, {'fieldtype': 'Currency'})} commission",
            "status": "submitted" if payment_entry.docstatus == 1 else "draft",
            "references_added": len(outstanding_invoices) if outstanding_invoices else 0
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating commission payment: {str(e)}")
        frappe.throw(f"Failed to create commission payment: {str(e)}")

def update_sales_invoice_commission_status(sales_partner, payment_amount):
    """Update commission status in related sales invoices when payment is made"""
    try:
        # Get all unpaid sales invoices for this sales partner
        unpaid_invoices = frappe.db.sql("""
            SELECT name, dlits_commission_amount, dlits_commission_paid_amount
            FROM `tabSales Invoice`
            WHERE dlits_sales_partner = %s
            AND docstatus = 1
            AND (dlits_commission_paid_amount IS NULL OR dlits_commission_paid_amount < dlits_commission_amount)
            ORDER BY posting_date ASC
        """, (sales_partner,), as_dict=True)
        
        remaining_payment = flt(payment_amount)
        
        for invoice in unpaid_invoices:
            if remaining_payment <= 0:
                break
                
            commission_amount = flt(invoice.dlits_commission_amount or 0)
            already_paid = flt(invoice.dlits_commission_paid_amount or 0)
            outstanding_commission = commission_amount - already_paid
            
            if outstanding_commission > 0:
                # Calculate how much to allocate to this invoice
                allocation = min(remaining_payment, outstanding_commission)
                new_paid_amount = already_paid + allocation
                
                # Update the sales invoice
                frappe.db.set_value("Sales Invoice", invoice.name, "dlits_commission_paid_amount", new_paid_amount)
                
                remaining_payment -= allocation
                
                frappe.msgprint(f"Updated commission payment for {invoice.name}: {frappe.format(allocation, {'fieldtype': 'Currency'})}")
        
        return True
        
    except Exception as e:
        frappe.log_error(f"Error updating sales invoice commission status: {str(e)}")
        return False

@frappe.whitelist()
def create_commission_journal_entry(sales_partner, amount, reference_doc=None):
    """Create Journal Entry for commission accrual"""
    try:
        partner = frappe.get_doc("DLITS Sales Partner", sales_partner)
        
        # Ensure supplier exists
        if not partner.supplier:
            if partner.auto_create_supplier:
                partner.create_supplier()
                partner.reload()
            else:
                frappe.throw("No supplier linked. Please create or link a supplier first.")
        
        # Get default company
        company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
        if not company:
            company = frappe.db.get_value("Company", {}, "name")
        
        # Get default accounts
        company_doc = frappe.get_doc("Company", company)
        
        # Get expense account (Commission Expense)
        expense_account = company_doc.default_expense_account
        if not expense_account:
            expense_account = frappe.db.get_value("Account", {
                "account_type": "Expense Account",
                "company": company,
                "is_group": 0
            }, "name")
        
        # Get payable account
        payable_account = company_doc.default_payable_account
        if not payable_account:
            payable_account = frappe.db.get_value("Account", {
                "account_type": "Payable",
                "company": company,
                "is_group": 0
            }, "name")
        
        if not expense_account or not payable_account:
            frappe.throw("Default expense and payable accounts must be configured in Company settings")
        
        # Create Journal Entry
        journal_entry = frappe.get_doc({
            "doctype": "Journal Entry",
            "voucher_type": "Journal Entry",
            "company": company,
            "posting_date": nowdate(),
            "user_remark": f"Commission accrual for DLITS Sales Partner: {partner.partner_name}",
            "accounts": [
                {
                    "account": expense_account,
                    "debit_in_account_currency": flt(amount),
                    "credit_in_account_currency": 0,
                    "user_remark": f"Commission expense for {partner.partner_name}"
                },
                {
                    "account": payable_account,
                    "party_type": "Supplier",
                    "party": partner.supplier,
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": flt(amount),
                    "user_remark": f"Commission payable to {partner.partner_name}"
                }
            ]
        })
        
        if reference_doc:
            journal_entry.user_remark += f" - Reference: {reference_doc}"
        
        # Save as draft for user review
        journal_entry.insert(ignore_permissions=True)
        
        return {
            "journal_entry": journal_entry,
            "message": f"Journal Entry {journal_entry.name} created as draft for {frappe.format(amount, {'fieldtype': 'Currency'})} commission accrual"
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating commission journal entry: {str(e)}")
        frappe.throw(f"Failed to create commission journal entry: {str(e)}")

@frappe.whitelist()
def get_commission_summary(sales_partner, from_date=None, to_date=None):
    """Get commission summary for a sales partner"""
    partner = frappe.get_doc("DLITS Sales Partner", sales_partner)
    return partner.get_commission_summary(from_date, to_date)

@frappe.whitelist()
def create_supplier(sales_partner):
    """Create supplier for sales partner"""
    partner = frappe.get_doc("DLITS Sales Partner", sales_partner)
    partner.create_supplier()
    return {"message": f"Supplier created successfully for {partner.partner_name}"}

@frappe.whitelist()
def update_partner_totals(sales_partner):
    """Update sales partner commission totals"""
    partner = frappe.get_doc("DLITS Sales Partner", sales_partner)
    partner.update_commission_totals()
    
    return {
        "total_sales": partner.total_sales,
        "total_commission_earned": partner.total_commission_earned,
        "total_commission_paid": partner.total_commission_paid,
        "outstanding_commission": partner.outstanding_commission
    }

@frappe.whitelist()
def debug_payment_tracking(sales_partner):
    """Debug function to check payment tracking for a sales partner"""
    try:
        partner = frappe.get_doc("DLITS Sales Partner", sales_partner)
        
        debug_info = {
            "sales_partner": sales_partner,
            "partner_name": partner.partner_name,
            "supplier": partner.supplier,
            "supplier_exists": bool(partner.supplier),
            "payments_found": [],
            "payment_queries": []
        }
        
        if partner.supplier:
            # Check what payments exist for this supplier
            all_payments = frappe.db.sql("""
                SELECT name, party, party_type, paid_amount, remarks, reference_no, docstatus
                FROM `tabPayment Entry`
                WHERE party = %s
                ORDER BY creation DESC
            """, (partner.supplier,), as_dict=True)
            
            debug_info["all_payments_for_supplier"] = all_payments
            
            # Test our current query patterns
            query1 = frappe.db.sql("""
                SELECT name, paid_amount, remarks, reference_no, docstatus
                FROM `tabPayment Entry`
                WHERE party = %s
                AND party_type = 'Supplier'
                AND docstatus = 1
                AND (remarks LIKE %s OR remarks LIKE %s OR reference_no LIKE %s)
            """, (partner.supplier,
                  f"%Commission payment for Sales Partner: {partner.partner_name}%",
                  f"%Commission%{sales_partner}%",
                  f"%Commission-{sales_partner}%"), as_dict=True)
            
            debug_info["query1_results"] = query1
            debug_info["query1_sql"] = f"Looking for supplier: {partner.supplier}, patterns: Commission payment for Sales Partner: {partner.partner_name}, Commission%{sales_partner}%, Commission-{sales_partner}%"
            
            # Test broader patterns
            query2 = frappe.db.sql("""
                SELECT name, paid_amount, remarks, reference_no, docstatus
                FROM `tabPayment Entry`
                WHERE party = %s
                AND party_type = 'Supplier'
                AND (remarks LIKE %s OR reference_no LIKE %s)
            """, (partner.supplier, "%Commission%", "%Commission%"), as_dict=True)
            
            debug_info["query2_results"] = query2
            
        else:
            debug_info["error"] = "No supplier linked to sales partner"
        
        return debug_info
        
    except Exception as e:
        return {"error": str(e)}
@frappe.whitelist()
def update_existing_commission_payments(sales_partner):
    """Update commission status for existing payments - one-time fix function"""
    try:
        partner = frappe.get_doc("DLITS Sales Partner", sales_partner)
        
        # Get all submitted payments for this sales partner
        payments = frappe.db.sql("""
            SELECT name, paid_amount, reference_date
            FROM `tabPayment Entry`
            WHERE docstatus = 1
            AND (
                (party_type = 'Supplier' AND party = %s) OR
                (party = %s)
            )
            AND (remarks LIKE %s OR reference_no LIKE %s)
            ORDER BY reference_date ASC
        """, (partner.supplier, f"{sales_partner} (Sales Partner)",
              f"%Commission%{sales_partner}%", f"%Commission%{sales_partner}%"), as_dict=True)
        
        total_updated = 0
        for payment in payments:
            # Update sales invoice commission status for this payment
            if update_sales_invoice_commission_status(sales_partner, payment.paid_amount):
                total_updated += payment.paid_amount
        
        # Update partner totals
        partner.update_commission_totals()
        
        return {
            "message": f"Updated commission payments totaling {frappe.format(total_updated, {'fieldtype': 'Currency'})}",
            "payments_processed": len(payments),
            "total_amount": total_updated
        }
        
    except Exception as e:
        frappe.log_error(f"Error updating existing commission payments: {str(e)}")
        return {"error": str(e)}