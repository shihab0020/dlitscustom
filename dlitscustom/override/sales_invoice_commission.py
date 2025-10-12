# Copyright (c) 2024, DLITS and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt

def validate_sales_invoice_commission(doc, method):
    """Validate and calculate commission for Sales Invoice"""
    if doc.dlits_sales_partner:
        calculate_commission(doc)
        validate_commission_fields(doc)

def on_submit_sales_invoice_commission(doc, method):
    """Update sales partner totals when invoice is submitted"""
    if doc.dlits_sales_partner and doc.dlits_commission_amount:
        update_sales_partner_totals(doc.dlits_sales_partner)

def on_cancel_sales_invoice_commission(doc, method):
    """Update sales partner totals when invoice is cancelled"""
    if doc.dlits_sales_partner and doc.dlits_commission_amount:
        update_sales_partner_totals(doc.dlits_sales_partner)

def calculate_commission(doc):
    """Calculate commission amount based on sales partner configuration or manual input"""
    if not doc.dlits_sales_partner:
        return
    
    try:
        # Get sales partner details
        sales_partner = frappe.get_doc("DLITS Sales Partner", doc.dlits_sales_partner)
        
        # Check if partner is active
        if sales_partner.status != "Active":
            frappe.throw(f"Sales Partner {sales_partner.partner_name} is not active")
        
        # Set commission type from sales partner (default)
        if not doc.dlits_commission_type:
            doc.dlits_commission_type = sales_partner.commission_type
        
        # Calculate commission based on manual input or default rate
        base_amount = flt(doc.grand_total)
        commission_amount = 0
        
        # If commission amount is manually entered, calculate rate
        if doc.dlits_commission_amount and not doc.dlits_commission_rate:
            commission_amount = flt(doc.dlits_commission_amount)
            if base_amount > 0:
                doc.dlits_commission_rate = (commission_amount / base_amount) * 100
        
        # If commission rate is manually entered, calculate amount
        elif doc.dlits_commission_rate:
            if doc.dlits_commission_type == "Percentage":
                commission_amount = base_amount * flt(doc.dlits_commission_rate) / 100
            else:  # Fixed Amount
                commission_amount = flt(doc.dlits_commission_rate)
            doc.dlits_commission_amount = commission_amount
        
        # If neither is entered, use sales partner defaults
        else:
            doc.dlits_commission_rate = sales_partner.commission_rate
            if sales_partner.commission_type == "Percentage":
                commission_amount = base_amount * flt(sales_partner.commission_rate) / 100
            else:  # Fixed Amount
                commission_amount = flt(sales_partner.commission_rate)
            doc.dlits_commission_amount = commission_amount
        
        # Apply minimum and maximum limits (only if using default calculation)
        if not (doc.dlits_commission_amount and doc.dlits_commission_rate != sales_partner.commission_rate):
            if sales_partner.minimum_commission and commission_amount < flt(sales_partner.minimum_commission):
                commission_amount = flt(sales_partner.minimum_commission)
                doc.dlits_commission_amount = commission_amount
            
            if sales_partner.maximum_commission and commission_amount > flt(sales_partner.maximum_commission):
                commission_amount = flt(sales_partner.maximum_commission)
                doc.dlits_commission_amount = commission_amount
        
        # Calculate outstanding commission
        doc.dlits_commission_outstanding = flt(doc.dlits_commission_amount) - flt(doc.dlits_commission_paid_amount or 0)
        
        # Log commission calculation
        frappe.logger().info(f"Commission calculated for {doc.name}: {commission_amount} for partner {sales_partner.partner_name}")
        
    except Exception as e:
        frappe.log_error(f"Error calculating commission for {doc.name}: {str(e)}")
        frappe.throw(f"Error calculating commission: {str(e)}")

def validate_commission_fields(doc):
    """Validate commission-related fields"""
    if doc.dlits_commission_paid_amount and flt(doc.dlits_commission_paid_amount) > flt(doc.dlits_commission_amount):
        frappe.throw("Commission paid amount cannot be greater than commission amount")
    
    if doc.dlits_commission_paid_amount and flt(doc.dlits_commission_paid_amount) < 0:
        frappe.throw("Commission paid amount cannot be negative")

def update_sales_partner_totals(sales_partner_name):
    """Update sales partner commission totals"""
    try:
        sales_partner = frappe.get_doc("DLITS Sales Partner", sales_partner_name)
        sales_partner.update_commission_totals()
        frappe.logger().info(f"Updated commission totals for {sales_partner_name}")
    except Exception as e:
        frappe.log_error(f"Error updating sales partner totals for {sales_partner_name}: {str(e)}")

@frappe.whitelist()
def get_sales_partner_details(sales_partner):
    """Get sales partner details for commission calculation"""
    if not sales_partner:
        return {}
    
    try:
        partner = frappe.get_doc("DLITS Sales Partner", sales_partner)
        return {
            "commission_type": partner.commission_type,
            "commission_rate": partner.commission_rate,
            "minimum_commission": partner.minimum_commission,
            "maximum_commission": partner.maximum_commission,
            "status": partner.status
        }
    except Exception as e:
        frappe.log_error(f"Error getting sales partner details: {str(e)}")
        return {}

@frappe.whitelist()
def calculate_commission_amount(sales_partner, grand_total):
    """Calculate commission amount for given parameters"""
    if not sales_partner or not grand_total:
        return 0
    
    try:
        partner = frappe.get_doc("DLITS Sales Partner", sales_partner)
        base_amount = flt(grand_total)
        
        if partner.commission_type == "Percentage":
            commission = base_amount * flt(partner.commission_rate) / 100
        else:  # Fixed Amount
            commission = flt(partner.commission_rate)
        
        # Apply limits
        if partner.minimum_commission and commission < flt(partner.minimum_commission):
            commission = flt(partner.minimum_commission)
        
        if partner.maximum_commission and commission > flt(partner.maximum_commission):
            commission = flt(partner.maximum_commission)
        
        return commission
        
    except Exception as e:
        frappe.log_error(f"Error calculating commission amount: {str(e)}")
        return 0

@frappe.whitelist()
def update_commission_paid_amount(invoice_name, paid_amount):
    """Update commission paid amount for an invoice"""
    try:
        doc = frappe.get_doc("Sales Invoice", invoice_name)
        
        if flt(paid_amount) > flt(doc.dlits_commission_amount):
            frappe.throw("Paid amount cannot be greater than commission amount")
        
        if flt(paid_amount) < 0:
            frappe.throw("Paid amount cannot be negative")
        
        doc.db_set("dlits_commission_paid_amount", flt(paid_amount))
        doc.db_set("dlits_commission_outstanding", flt(doc.dlits_commission_amount) - flt(paid_amount))
        
        # Update sales partner totals
        if doc.dlits_sales_partner:
            update_sales_partner_totals(doc.dlits_sales_partner)
        
        return {
            "success": True,
            "message": f"Commission paid amount updated to {paid_amount}",
            "outstanding": flt(doc.dlits_commission_amount) - flt(paid_amount)
        }
        
    except Exception as e:
        frappe.log_error(f"Error updating commission paid amount: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist()
def get_unpaid_commission_invoices(sales_partner=None, from_date=None, to_date=None):
    """Get invoices with unpaid commission"""
    conditions = ["docstatus = 1", "dlits_commission_outstanding > 0"]
    values = []
    
    if sales_partner:
        conditions.append("dlits_sales_partner = %s")
        values.append(sales_partner)
    
    if from_date:
        conditions.append("posting_date >= %s")
        values.append(from_date)
    
    if to_date:
        conditions.append("posting_date <= %s")
        values.append(to_date)
    
    where_clause = " AND ".join(conditions)
    
    invoices = frappe.db.sql(f"""
        SELECT 
            name,
            posting_date,
            customer,
            dlits_sales_partner,
            grand_total,
            dlits_commission_amount,
            dlits_commission_paid_amount,
            dlits_commission_outstanding
        FROM `tabSales Invoice`
        WHERE {where_clause}
        ORDER BY posting_date DESC
    """, values, as_dict=True)
    
    return invoices

@frappe.whitelist()
def create_bulk_commission_payment(invoices, sales_partner):
    """Create bulk commission payment for multiple invoices"""
    try:
        if not invoices or not sales_partner:
            frappe.throw("Invoices and sales partner are required")
        
        invoice_list = frappe.parse_json(invoices) if isinstance(invoices, str) else invoices
        
        total_amount = 0
        invoice_names = []
        
        for invoice_name in invoice_list:
            invoice = frappe.get_doc("Sales Invoice", invoice_name)
            if invoice.dlits_sales_partner == sales_partner and invoice.dlits_commission_outstanding > 0:
                total_amount += flt(invoice.dlits_commission_outstanding)
                invoice_names.append(invoice_name)
        
        if total_amount == 0:
            frappe.throw("No outstanding commission found for selected invoices")
        
        # Create payment entry
        partner = frappe.get_doc("DLITS Sales Partner", sales_partner)
        payment_entry = partner.create_commission_payment_entry(
            total_amount, 
            f"Bulk payment for invoices: {', '.join(invoice_names)}"
        )
        
        return {
            "success": True,
            "payment_entry": payment_entry.name,
            "amount": total_amount,
            "invoices": invoice_names
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating bulk commission payment: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist()
def adjust_commission_after_submit(invoice_name, commission_amount=None, commission_rate=None):
    """Allow manual adjustment of commission after invoice submission"""
    try:
        doc = frappe.get_doc("Sales Invoice", invoice_name)
        
        if doc.docstatus != 1:
            frappe.throw("Invoice must be submitted to adjust commission")
        
        if not doc.dlits_sales_partner:
            frappe.throw("No DLITS Sales Partner assigned to this invoice")
        
        # Get sales partner details
        sales_partner = frappe.get_doc("DLITS Sales Partner", doc.dlits_sales_partner)
        base_amount = flt(doc.grand_total)
        
        # Calculate new commission based on input
        if commission_amount:
            new_commission_amount = flt(commission_amount)
            if base_amount > 0:
                new_commission_rate = (new_commission_amount / base_amount) * 100
            else:
                new_commission_rate = 0
        elif commission_rate:
            new_commission_rate = flt(commission_rate)
            if doc.dlits_commission_type == "Percentage":
                new_commission_amount = base_amount * new_commission_rate / 100
            else:
                new_commission_amount = new_commission_rate
        else:
            frappe.throw("Either commission amount or commission rate must be provided")
        
        # Validate the new values
        if new_commission_amount < 0:
            frappe.throw("Commission amount cannot be negative")
        
        if new_commission_rate < 0:
            frappe.throw("Commission rate cannot be negative")
        
        # Update the invoice
        old_commission = flt(doc.dlits_commission_amount)
        doc.db_set("dlits_commission_amount", new_commission_amount)
        doc.db_set("dlits_commission_rate", new_commission_rate)
        
        # Recalculate outstanding commission
        outstanding = new_commission_amount - flt(doc.dlits_commission_paid_amount or 0)
        doc.db_set("dlits_commission_outstanding", outstanding)
        
        # Update sales partner totals
        update_sales_partner_totals(doc.dlits_sales_partner)
        
        # Log the adjustment
        frappe.logger().info(f"Commission adjusted for {invoice_name}: {old_commission} -> {new_commission_amount}")
        
        return {
            "success": True,
            "message": f"Commission adjusted from {frappe.format(old_commission, {'fieldtype': 'Currency'})} to {frappe.format(new_commission_amount, {'fieldtype': 'Currency'})}",
            "old_commission": old_commission,
            "new_commission": new_commission_amount,
            "new_rate": new_commission_rate,
            "outstanding": outstanding
        }
        
    except Exception as e:
        frappe.log_error(f"Error adjusting commission for {invoice_name}: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist()
def recalculate_commission_from_rate(invoice_name, commission_rate):
    """Recalculate commission amount from rate"""
    try:
        doc = frappe.get_doc("Sales Invoice", invoice_name)
        base_amount = flt(doc.grand_total)
        
        if doc.dlits_commission_type == "Percentage":
            commission_amount = base_amount * flt(commission_rate) / 100
        else:
            commission_amount = flt(commission_rate)
        
        return {
            "commission_amount": commission_amount,
            "commission_rate": flt(commission_rate)
        }
        
    except Exception as e:
        return {
            "error": str(e)
        }

@frappe.whitelist()
def recalculate_commission_from_amount(invoice_name, commission_amount):
    """Recalculate commission rate from amount"""
    try:
        doc = frappe.get_doc("Sales Invoice", invoice_name)
        base_amount = flt(doc.grand_total)
        
        if base_amount > 0:
            commission_rate = (flt(commission_amount) / base_amount) * 100
        else:
            commission_rate = 0
        
        return {
            "commission_amount": flt(commission_amount),
            "commission_rate": commission_rate
        }
        
    except Exception as e:
        return {
            "error": str(e)
        }