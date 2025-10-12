import frappe
from frappe import _

@frappe.whitelist()
def create_dlits_workspace_direct():
    """Create DLITS Custom Workspace using direct SQL approach"""
    
    try:
        # Check if workspace already exists
        if frappe.db.exists("Workspace", "DLITS Custom"):
            frappe.db.sql("DELETE FROM `tabWorkspace` WHERE name = 'DLITS Custom'")
            frappe.db.sql("DELETE FROM `tabWorkspace Shortcut` WHERE parent = 'DLITS Custom'")
            frappe.db.sql("DELETE FROM `tabWorkspace Card` WHERE parent = 'DLITS Custom'")
            frappe.db.sql("DELETE FROM `tabWorkspace Link` WHERE parent IN (SELECT name FROM `tabWorkspace Card` WHERE parent = 'DLITS Custom')")
            print("Deleted existing workspace")
        
        # Insert workspace
        frappe.db.sql("""
            INSERT INTO `tabWorkspace` 
            (name, title, category, icon, indicator_color, is_hidden, public, module, owner, creation, modified, modified_by, docstatus, idx)
            VALUES 
            ('DLITS Custom', 'DLITS Custom', 'Modules', 'fa fa-cogs', 'orange', 0, 1, 'dlitscustom', 'Administrator', NOW(), NOW(), 'Administrator', 0, 0)
        """)
        
        # Insert shortcuts
        shortcuts = [
            ('Pricing Rule Dlits', 'Pricing Rule Dlits', 'DocType', 'fa fa-tags', '#3498db', 'Advanced pricing rules'),
            ('Sales Partner', 'Sales Partner', 'DocType', 'fa fa-handshake-o', '#e74c3c', 'Sales partner management'),
            ('Payment Entry', 'Payment Entry', 'DocType', 'fa fa-credit-card', '#34495e', 'Commission payments'),
            ('Sales Order', 'Sales Order', 'DocType', 'fa fa-file-text-o', '#f39c12', 'Sales orders'),
            ('Sales Invoice', 'Sales Invoice', 'DocType', 'fa fa-file-text', '#27ae60', 'Sales invoices'),
            ('Item Price', 'Item Price', 'DocType', 'fa fa-money', '#8e44ad', 'Item pricing')
        ]
        
        for i, (label, link_to, type_val, icon, color, description) in enumerate(shortcuts):
            frappe.db.sql("""
                INSERT INTO `tabWorkspace Shortcut`
                (name, parent, parenttype, parentfield, label, link_to, type, icon, color, description, owner, creation, modified, modified_by, docstatus, idx)
                VALUES
                (%s, 'DLITS Custom', 'Workspace', 'shortcuts', %s, %s, %s, %s, %s, %s, 'Administrator', NOW(), NOW(), 'Administrator', 0, %s)
            """, (f"shortcut-{i+1}", label, link_to, type_val, icon, color, description, i+1))
        
        frappe.db.commit()
        
        print("Successfully created DLITS Custom workspace")
        return {
            "success": True,
            "message": "Workspace created successfully",
            "workspace_name": "DLITS Custom"
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating workspace: {str(e)}", "Workspace Creation")
        print(f"Error creating workspace: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def check_workspace_exists():
    """Check if DLITS Custom workspace exists"""
    exists = frappe.db.exists("Workspace", "DLITS Custom")
    print(f"DLITS Custom workspace exists: {exists}")
    
    if exists:
        shortcuts = frappe.db.sql("""
            SELECT label, link_to, type FROM `tabWorkspace Shortcut` 
            WHERE parent = 'DLITS Custom'
            ORDER BY idx
        """, as_dict=True)
        print(f"Found {len(shortcuts)} shortcuts:")
        for shortcut in shortcuts:
            print(f"  - {shortcut.label} ({shortcut.type}: {shortcut.link_to})")
    
    return {"exists": bool(exists), "shortcuts": shortcuts if exists else []}