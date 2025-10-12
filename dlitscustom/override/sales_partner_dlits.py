import frappe
from frappe import _

def sales_partner_after_insert(doc, method=None):
    """
    Automatically create a Supplier when a Sales Partner is created
    """
    try:
        # Check if supplier already exists with same name
        existing_supplier = frappe.db.exists("Supplier", doc.partner_name)
        
        if existing_supplier:
            # Link existing supplier to sales partner
            frappe.db.set_value("Supplier", existing_supplier, "sales_partner_link", doc.name)
            frappe.db.commit()
            frappe.msgprint(
                _("Existing Supplier '{0}' has been linked to Sales Partner '{1}'").format(
                    existing_supplier, doc.partner_name
                ),
                title=_("Supplier Linked"),
                indicator="green"
            )
        else:
            # Create new supplier
            supplier_doc = frappe.get_doc({
                "doctype": "Supplier",
                "supplier_name": doc.partner_name,
                "supplier_group": get_default_supplier_group(),
                "supplier_type": "Individual" if doc.partner_type == "Individual" else "Company",
                "sales_partner_link": doc.name,
                "is_frozen": 0
            })
            
            # Copy contact details if available
            if hasattr(doc, 'email_id') and doc.email_id:
                supplier_doc.email_id = doc.email_id
            if hasattr(doc, 'mobile_no') and doc.mobile_no:
                supplier_doc.mobile_no = doc.mobile_no
            if hasattr(doc, 'address') and doc.address:
                supplier_doc.address_line1 = doc.address
                
            supplier_doc.insert(ignore_permissions=True)
            frappe.db.commit()
            
            frappe.msgprint(
                _("Supplier '{0}' has been created and linked to Sales Partner '{1}'").format(
                    supplier_doc.name, doc.partner_name
                ),
                title=_("Supplier Created"),
                indicator="green"
            )
            
    except Exception as e:
        frappe.log_error(f"Error creating supplier for sales partner {doc.name}: {str(e)}")
        frappe.msgprint(
            _("Error creating supplier: {0}").format(str(e)),
            title=_("Error"),
            indicator="red"
        )

def sales_partner_on_update(doc, method=None):
    """
    Update linked supplier when sales partner is updated
    """
    try:
        # Find linked supplier
        linked_supplier = frappe.db.get_value("Supplier", {"sales_partner_link": doc.name}, "name")
        
        if linked_supplier:
            # Update supplier details
            supplier_doc = frappe.get_doc("Supplier", linked_supplier)
            supplier_doc.supplier_name = doc.partner_name
            
            # Update contact details if available
            if hasattr(doc, 'email_id') and doc.email_id:
                supplier_doc.email_id = doc.email_id
            if hasattr(doc, 'mobile_no') and doc.mobile_no:
                supplier_doc.mobile_no = doc.mobile_no
                
            supplier_doc.save(ignore_permissions=True)
            frappe.db.commit()
            
    except Exception as e:
        frappe.log_error(f"Error updating supplier for sales partner {doc.name}: {str(e)}")

def get_default_supplier_group():
    """
    Get default supplier group for sales partners
    """
    # Try to get "Sales Partners" supplier group, create if doesn't exist
    supplier_group = frappe.db.exists("Supplier Group", "Sales Partners")
    
    if not supplier_group:
        try:
            sg_doc = frappe.get_doc({
                "doctype": "Supplier Group",
                "supplier_group_name": "Sales Partners",
                "parent_supplier_group": frappe.db.get_single_value("Buying Settings", "supplier_group") or "All Supplier Groups"
            })
            sg_doc.insert(ignore_permissions=True)
            frappe.db.commit()
            return "Sales Partners"
        except:
            # Fallback to default supplier group
            return frappe.db.get_single_value("Buying Settings", "supplier_group") or "All Supplier Groups"
    
    return "Sales Partners"

@frappe.whitelist()
def get_sales_partner_supplier(sales_partner):
    """
    Get linked supplier for a sales partner
    """
    if not sales_partner:
        return None
        
    supplier = frappe.db.get_value("Supplier", {"sales_partner_link": sales_partner}, "name")
    return supplier

@frappe.whitelist()
def create_commission_payment_entry(sales_partner, amount, reference_date=None):
    """
    Create payment entry for sales partner commission
    """
    try:
        # Get linked supplier
        supplier = get_sales_partner_supplier(sales_partner)
        
        if not supplier:
            frappe.throw(_("No linked supplier found for Sales Partner {0}").format(sales_partner))
        
        # Create payment entry
        payment_entry = frappe.get_doc({
            "doctype": "Payment Entry",
            "payment_type": "Pay",
            "party_type": "Supplier",
            "party": supplier,
            "paid_amount": amount,
            "received_amount": amount,
            "reference_date": reference_date or frappe.utils.today(),
            "remarks": f"Commission payment for Sales Partner: {sales_partner}"
        })
        
        return payment_entry.as_dict()
        
    except Exception as e:
        frappe.throw(_("Error creating payment entry: {0}").format(str(e)))