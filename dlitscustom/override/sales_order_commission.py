# Copyright (c) 2024, DLITS and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt

def validate_sales_order_commission(doc, method):
    """Validate and calculate commission for Sales Order"""
    if doc.dlits_sales_partner:
        calculate_commission(doc)

def calculate_commission(doc):
    """Calculate commission amount based on sales partner configuration"""
    if not doc.dlits_sales_partner:
        return
    
    try:
        # Get sales partner details
        sales_partner = frappe.get_doc("DLITS Sales Partner", doc.dlits_sales_partner)
        
        # Check if partner is active
        if sales_partner.status != "Active":
            frappe.throw(f"Sales Partner {sales_partner.partner_name} is not active")
        
        # Set commission type and rate from sales partner
        doc.dlits_commission_type = sales_partner.commission_type
        doc.dlits_commission_rate = sales_partner.commission_rate
        
        # Calculate commission amount
        base_amount = flt(doc.grand_total)
        
        if sales_partner.commission_type == "Percentage":
            commission_amount = base_amount * flt(sales_partner.commission_rate) / 100
        else:  # Fixed Amount
            commission_amount = flt(sales_partner.commission_rate)
        
        # Apply minimum and maximum limits
        if sales_partner.minimum_commission and commission_amount < flt(sales_partner.minimum_commission):
            commission_amount = flt(sales_partner.minimum_commission)
        
        if sales_partner.maximum_commission and commission_amount > flt(sales_partner.maximum_commission):
            commission_amount = flt(sales_partner.maximum_commission)
        
        # Set commission amount
        doc.dlits_commission_amount = commission_amount
        
        # Log commission calculation
        frappe.logger().info(f"Commission calculated for Sales Order {doc.name}: {commission_amount} for partner {sales_partner.partner_name}")
        
    except Exception as e:
        frappe.log_error(f"Error calculating commission for Sales Order {doc.name}: {str(e)}")
        frappe.throw(f"Error calculating commission: {str(e)}")

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