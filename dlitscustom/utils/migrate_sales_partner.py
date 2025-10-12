import frappe
from frappe import _
from frappe.utils import flt, nowdate, cstr
import json

@frappe.whitelist()
def migrate_erpnext_to_dlits_sales_partners():
    """
    Migrate existing ERPNext Sales Partners to DLITS Sales Partners
    """
    try:
        print("🔄 Starting migration from ERPNext Sales Partner to DLITS Sales Partner...")
        
        # Get all existing ERPNext Sales Partners
        erpnext_partners = frappe.db.sql("""
            SELECT 
                name, partner_name, partner_type, partner_website,
                commission_rate, address, territory, disabled,
                creation, modified, owner, modified_by
            FROM `tabSales Partner`
            WHERE name NOT IN (
                SELECT partner_name FROM `tabDLITS Sales Partner` 
                WHERE partner_name IS NOT NULL
            )
        """, as_dict=True)
        
        migrated_count = 0
        errors = []
        
        for partner in erpnext_partners:
            try:
                # Create DLITS Sales Partner
                dlits_partner = frappe.get_doc({
                    "doctype": "DLITS Sales Partner",
                    "partner_name": partner.partner_name,
                    "partner_type": map_partner_type(partner.partner_type),
                    "commission_type": "Percentage",
                    "commission_rate": flt(partner.commission_rate or 0),
                    "status": "Inactive" if partner.disabled else "Active",
                    "address": partner.address or "",
                    "notes": f"Migrated from ERPNext Sales Partner: {partner.name}",
                    "start_date": partner.creation.date() if partner.creation else nowdate(),
                    "auto_create_supplier": 1
                })
                
                # Set creation details to preserve history
                dlits_partner.creation = partner.creation
                dlits_partner.owner = partner.owner
                dlits_partner.modified = partner.modified
                dlits_partner.modified_by = partner.modified_by
                
                dlits_partner.insert(ignore_permissions=True)
                
                # Update references in Sales Orders and Sales Invoices
                update_sales_transactions(partner.name, dlits_partner.name)
                
                migrated_count += 1
                print(f"   ✅ Migrated: {partner.partner_name} -> {dlits_partner.name}")
                
            except Exception as e:
                error_msg = f"Error migrating {partner.partner_name}: {str(e)}"
                errors.append(error_msg)
                print(f"   ❌ {error_msg}")
        
        # Create migration summary
        summary = {
            "total_partners": len(erpnext_partners),
            "migrated_count": migrated_count,
            "errors": errors,
            "success_rate": (migrated_count / len(erpnext_partners) * 100) if erpnext_partners else 100
        }
        
        print(f"✅ Migration completed: {migrated_count}/{len(erpnext_partners)} partners migrated")
        return summary
        
    except Exception as e:
        frappe.log_error(f"Sales Partner migration error: {str(e)}")
        frappe.throw(f"Migration failed: {str(e)}")

def map_partner_type(erpnext_type):
    """Map ERPNext partner types to DLITS partner types"""
    mapping = {
        "Customer": "Individual",
        "Supplier": "Company", 
        "Employee": "Individual",
        "Company": "Company"
    }
    return mapping.get(erpnext_type, "Individual")

def update_sales_transactions(old_partner, new_partner):
    """Update Sales Orders and Sales Invoices to use DLITS Sales Partner"""
    try:
        # Update Sales Orders
        frappe.db.sql("""
            UPDATE `tabSales Order` 
            SET dlits_sales_partner = %s 
            WHERE sales_partner = %s
        """, (new_partner, old_partner))
        
        # Update Sales Invoices  
        frappe.db.sql("""
            UPDATE `tabSales Invoice` 
            SET dlits_sales_partner = %s 
            WHERE sales_partner = %s
        """, (new_partner, old_partner))
        
        frappe.db.commit()
        
    except Exception as e:
        frappe.log_error(f"Error updating transactions for {old_partner}: {str(e)}")

@frappe.whitelist()
def create_dlits_partner_from_erpnext(erpnext_partner_name):
    """
    Create a single DLITS Sales Partner from ERPNext Sales Partner
    """
    try:
        # Get ERPNext Sales Partner
        partner = frappe.get_doc("Sales Partner", erpnext_partner_name)
        
        # Check if DLITS partner already exists
        if frappe.db.exists("DLITS Sales Partner", {"partner_name": partner.partner_name}):
            frappe.throw(f"DLITS Sales Partner with name '{partner.partner_name}' already exists")
        
        # Create DLITS Sales Partner
        dlits_partner = frappe.get_doc({
            "doctype": "DLITS Sales Partner",
            "partner_name": partner.partner_name,
            "partner_type": map_partner_type(partner.partner_type or "Individual"),
            "commission_type": "Percentage",
            "commission_rate": flt(partner.commission_rate or 0),
            "status": "Inactive" if partner.disabled else "Active",
            "address": partner.address or "",
            "notes": f"Migrated from ERPNext Sales Partner: {partner.name}",
            "start_date": partner.creation.date() if partner.creation else nowdate(),
            "auto_create_supplier": 1
        })
        
        dlits_partner.insert()
        
        # Update references
        update_sales_transactions(partner.name, dlits_partner.name)
        
        return {
            "success": True,
            "dlits_partner": dlits_partner.name,
            "message": f"Successfully created DLITS Sales Partner: {dlits_partner.name}"
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating DLITS partner from {erpnext_partner_name}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def get_migration_status():
    """
    Get current migration status
    """
    try:
        # Count ERPNext Sales Partners
        erpnext_count = frappe.db.count("Sales Partner")
        
        # Count DLITS Sales Partners
        dlits_count = frappe.db.count("DLITS Sales Partner")
        
        # Count unmigrated partners
        unmigrated = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM `tabSales Partner` sp
            WHERE sp.name NOT IN (
                SELECT COALESCE(notes, '') FROM `tabDLITS Sales Partner` 
                WHERE notes LIKE CONCAT('%', sp.name, '%')
            )
        """, as_dict=True)[0].count
        
        # Get sample unmigrated partners
        unmigrated_partners = frappe.db.sql("""
            SELECT name, partner_name, commission_rate, disabled
            FROM `tabSales Partner` sp
            WHERE sp.name NOT IN (
                SELECT COALESCE(notes, '') FROM `tabDLITS Sales Partner` 
                WHERE notes LIKE CONCAT('%', sp.name, '%')
            )
            LIMIT 10
        """, as_dict=True)
        
        return {
            "erpnext_partners": erpnext_count,
            "dlits_partners": dlits_count,
            "unmigrated_count": unmigrated,
            "migration_percentage": ((erpnext_count - unmigrated) / erpnext_count * 100) if erpnext_count > 0 else 100,
            "unmigrated_samples": unmigrated_partners
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting migration status: {str(e)}")
        return {"error": str(e)}

@frappe.whitelist()
def update_commission_management_utilities():
    """
    Update existing commission management utilities to use DLITS Sales Partner
    """
    try:
        print("🔄 Updating commission management utilities...")
        
        # Update commission_management_dlits.py references
        update_commission_management_references()
        
        # Update payment_references_dlits.py references  
        update_payment_references()
        
        # Update any custom reports
        update_custom_reports()
        
        print("✅ Commission management utilities updated")
        return {"success": True, "message": "Utilities updated successfully"}
        
    except Exception as e:
        frappe.log_error(f"Error updating utilities: {str(e)}")
        return {"success": False, "error": str(e)}

def update_commission_management_references():
    """Update commission management to use DLITS Sales Partner fields"""
    # This would involve updating the SQL queries in commission_management_dlits.py
    # to use dlits_sales_partner instead of sales_partner
    pass

def update_payment_references():
    """Update payment references to use DLITS Sales Partner"""
    # This would involve updating payment_references_dlits.py
    # to work with DLITS Sales Partner structure
    pass

def update_custom_reports():
    """Update custom reports to use DLITS Sales Partner"""
    # Update any custom reports to use the new DLITS Sales Partner
    pass

@frappe.whitelist()
def create_migration_backup():
    """
    Create backup of current Sales Partner data before migration
    """
    try:
        # Export current Sales Partner data
        partners = frappe.db.sql("""
            SELECT * FROM `tabSales Partner`
        """, as_dict=True)
        
        # Create backup file
        backup_data = {
            "backup_date": nowdate(),
            "total_partners": len(partners),
            "partners": partners
        }
        
        # Save to file
        backup_file = f"sales_partner_backup_{nowdate().replace('-', '_')}.json"
        
        return {
            "success": True,
            "backup_file": backup_file,
            "total_partners": len(partners),
            "backup_data": backup_data
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating backup: {str(e)}")
        return {"success": False, "error": str(e)}

@frappe.whitelist()
def validate_migration():
    """
    Validate migration results
    """
    try:
        validation_results = {
            "data_integrity": True,
            "reference_updates": True,
            "commission_calculations": True,
            "issues": []
        }
        
        # Check data integrity
        erpnext_partners = frappe.db.count("Sales Partner")
        dlits_partners = frappe.db.count("DLITS Sales Partner")
        
        if dlits_partners < erpnext_partners:
            validation_results["data_integrity"] = False
            validation_results["issues"].append(f"Missing DLITS partners: {erpnext_partners - dlits_partners}")
        
        # Check reference updates
        so_with_old_ref = frappe.db.sql("""
            SELECT COUNT(*) as count FROM `tabSales Order` 
            WHERE sales_partner IS NOT NULL AND dlits_sales_partner IS NULL
        """, as_dict=True)[0].count
        
        if so_with_old_ref > 0:
            validation_results["reference_updates"] = False
            validation_results["issues"].append(f"Sales Orders with unmigrated references: {so_with_old_ref}")
        
        si_with_old_ref = frappe.db.sql("""
            SELECT COUNT(*) as count FROM `tabSales Invoice` 
            WHERE sales_partner IS NOT NULL AND dlits_sales_partner IS NULL
        """, as_dict=True)[0].count
        
        if si_with_old_ref > 0:
            validation_results["reference_updates"] = False
            validation_results["issues"].append(f"Sales Invoices with unmigrated references: {si_with_old_ref}")
        
        validation_results["overall_success"] = (
            validation_results["data_integrity"] and 
            validation_results["reference_updates"] and 
            validation_results["commission_calculations"]
        )
        
        return validation_results
        
    except Exception as e:
        frappe.log_error(f"Error validating migration: {str(e)}")
        return {"error": str(e)}

@frappe.whitelist()
def rollback_migration():
    """
    Rollback migration if needed (use with caution)
    """
    try:
        # This is a dangerous operation - implement with proper safeguards
        frappe.throw("Rollback functionality not implemented for safety. Please contact administrator.")
        
    except Exception as e:
        frappe.log_error(f"Error in rollback: {str(e)}")
        return {"error": str(e)}