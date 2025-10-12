import frappe
from frappe import _

@frappe.whitelist()
def create_dlits_workspace_correct():
    """Create DLITS Custom Workspace using correct table structure"""
    
    try:
        # Check if workspace already exists
        if frappe.db.exists("Workspace", "DLITS Custom"):
            frappe.db.sql("DELETE FROM `tabWorkspace` WHERE name = 'DLITS Custom'")
            frappe.db.sql("DELETE FROM `tabWorkspace Shortcut` WHERE parent = 'DLITS Custom'")
            print("Deleted existing workspace")
        
        # Insert workspace with correct fields
        frappe.db.sql("""
            INSERT INTO `tabWorkspace` 
            (name, label, title, module, icon, indicator_color, is_hidden, public, owner, creation, modified, modified_by, docstatus, idx, sequence_id)
            VALUES 
            ('DLITS Custom', 'DLITS Custom', 'DLITS Custom', 'dlitscustom', 'fa fa-cogs', 'orange', 0, 1, 'Administrator', NOW(), NOW(), 'Administrator', 0, 0, 10.0)
        """)
        
        # Insert shortcuts with correct fields
        shortcuts = [
            ('Pricing Rule Dlits', 'Pricing Rule Dlits', 'DocType', 'fa fa-tags', '#3498db'),
            ('Sales Partner', 'Sales Partner', 'DocType', 'fa fa-handshake-o', '#e74c3c'),
            ('Payment Entry', 'Payment Entry', 'DocType', 'fa fa-credit-card', '#34495e'),
            ('Sales Order', 'Sales Order', 'DocType', 'fa fa-file-text-o', '#f39c12'),
            ('Sales Invoice', 'Sales Invoice', 'DocType', 'fa fa-file-text', '#27ae60'),
            ('Item Price', 'Item Price', 'DocType', 'fa fa-money', '#8e44ad')
        ]
        
        for i, (label, link_to, type_val, icon, color) in enumerate(shortcuts):
            shortcut_name = f"dlits-shortcut-{i+1}"
            frappe.db.sql("""
                INSERT INTO `tabWorkspace Shortcut`
                (name, parent, parenttype, parentfield, label, link_to, type, icon, color, owner, creation, modified, modified_by, docstatus, idx)
                VALUES
                (%s, 'DLITS Custom', 'Workspace', 'shortcuts', %s, %s, %s, %s, %s, 'Administrator', NOW(), NOW(), 'Administrator', 0, %s)
            """, (shortcut_name, label, link_to, type_val, icon, color, i+1))
        
        frappe.db.commit()
        
        print("Successfully created DLITS Custom workspace")
        return {
            "success": True,
            "message": "DLITS Custom workspace created successfully! Please refresh your browser to see it.",
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
def check_workspace_final():
    """Check if DLITS Custom workspace exists and is visible"""
    
    try:
        # Check workspace
        workspace = frappe.db.sql("""
            SELECT name, label, title, module, icon, indicator_color, is_hidden, public
            FROM `tabWorkspace` 
            WHERE name = 'DLITS Custom'
        """, as_dict=True)
        
        if not workspace:
            return {"exists": False, "message": "Workspace does not exist"}
        
        workspace = workspace[0]
        
        # Check shortcuts
        shortcuts = frappe.db.sql("""
            SELECT label, link_to, type, icon, color
            FROM `tabWorkspace Shortcut` 
            WHERE parent = 'DLITS Custom'
            ORDER BY idx
        """, as_dict=True)
        
        print(f"DLITS Custom workspace found:")
        print(f"  - Label: {workspace.label}")
        print(f"  - Module: {workspace.module}")
        print(f"  - Hidden: {workspace.is_hidden}")
        print(f"  - Public: {workspace.public}")
        print(f"  - Icon: {workspace.icon}")
        print(f"  - Color: {workspace.indicator_color}")
        print(f"  - Shortcuts: {len(shortcuts)}")
        
        for shortcut in shortcuts:
            print(f"    * {shortcut.label} ({shortcut.type}: {shortcut.link_to}) - {shortcut.color}")
        
        return {
            "exists": True,
            "workspace": workspace,
            "shortcuts": shortcuts,
            "message": f"Workspace exists with {len(shortcuts)} shortcuts. It should be visible in your ERPNext interface."
        }
        
    except Exception as e:
        print(f"Error checking workspace: {str(e)}")
        return {"exists": False, "error": str(e)}