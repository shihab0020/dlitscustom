import frappe
from frappe import _

@frappe.whitelist()
def create_dlits_workspace():
    """Create DLITS Custom Workspace"""
    
    try:
        # Check if workspace already exists
        if frappe.db.exists("Workspace", "DLITS Custom"):
            print("Workspace 'DLITS Custom' already exists")
            return {"success": True, "message": "Workspace already exists"}
        
        # Create the workspace
        workspace = frappe.get_doc({
            "doctype": "Workspace",
            "name": "DLITS Custom",
            "title": "DLITS Custom",
            "category": "Modules",
            "icon": "fa fa-cogs",
            "indicator_color": "orange",
            "is_hidden": 0,
            "public": 1,
            "module": "dlitscustom",
            "content": """[
                {
                    "type": "header",
                    "data": {
                        "text": "DLITS Custom - Advanced Pricing & Commission Management",
                        "col": 12
                    }
                },
                {
                    "type": "shortcut",
                    "data": {
                        "shortcut_name": "Pricing Rule Dlits",
                        "col": 3
                    }
                },
                {
                    "type": "shortcut", 
                    "data": {
                        "shortcut_name": "Sales Partner",
                        "col": 3
                    }
                },
                {
                    "type": "shortcut",
                    "data": {
                        "shortcut_name": "Payment Entry",
                        "col": 3
                    }
                },
                {
                    "type": "shortcut",
                    "data": {
                        "shortcut_name": "Sales Order",
                        "col": 3
                    }
                },
                {
                    "type": "card",
                    "data": {
                        "card_name": "Pricing Management",
                        "col": 6
                    }
                },
                {
                    "type": "card",
                    "data": {
                        "card_name": "Commission Management", 
                        "col": 6
                    }
                }
            ]""",
            "shortcuts": [
                {
                    "label": "Pricing Rule Dlits",
                    "link_to": "Pricing Rule Dlits",
                    "type": "DocType",
                    "icon": "fa fa-tags",
                    "color": "#3498db",
                    "stats_filter": '{"docstatus": ["!=", 2]}',
                    "description": "Advanced pricing rules with multiple base price types"
                },
                {
                    "label": "Sales Partner",
                    "link_to": "Sales Partner", 
                    "type": "DocType",
                    "icon": "fa fa-handshake-o",
                    "color": "#e74c3c",
                    "stats_filter": '{"disabled": 0}',
                    "description": "Manage sales partners with commission tracking"
                },
                {
                    "label": "Payment Entry",
                    "link_to": "Payment Entry",
                    "type": "DocType",
                    "icon": "fa fa-credit-card",
                    "color": "#34495e",
                    "description": "Process commission payments"
                },
                {
                    "label": "Sales Order",
                    "link_to": "Sales Order",
                    "type": "DocType", 
                    "icon": "fa fa-file-text-o",
                    "color": "#f39c12",
                    "stats_filter": '{"docstatus": 1}',
                    "description": "Sales orders with pricing rules"
                }
            ],
            "cards": [
                {
                    "label": "Pricing Management",
                    "links": [
                        {
                            "label": "Pricing Rule Dlits",
                            "link_to": "Pricing Rule Dlits",
                            "link_type": "DocType",
                            "description": "Create and manage advanced pricing rules"
                        },
                        {
                            "label": "Item Price",
                            "link_to": "Item Price", 
                            "link_type": "DocType",
                            "description": "Standard item pricing"
                        },
                        {
                            "label": "Item",
                            "link_to": "Item",
                            "link_type": "DocType",
                            "description": "Manage items and pricing"
                        }
                    ]
                },
                {
                    "label": "Commission Management",
                    "links": [
                        {
                            "label": "Sales Partner",
                            "link_to": "Sales Partner",
                            "link_type": "DocType", 
                            "description": "Manage sales partners and commissions"
                        },
                        {
                            "label": "Commission Report",
                            "link_to": "DLITS Sales Partner Commission Report",
                            "link_type": "Report",
                            "description": "Track commissions and payments"
                        },
                        {
                            "label": "Payment Entry",
                            "link_to": "Payment Entry",
                            "link_type": "DocType",
                            "description": "Process commission payments"
                        }
                    ]
                }
            ]
        })
        
        workspace.insert(ignore_permissions=True)
        frappe.db.commit()
        
        print(f"Successfully created workspace: {workspace.name}")
        return {
            "success": True, 
            "message": f"Workspace '{workspace.name}' created successfully",
            "workspace_name": workspace.name
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating workspace: {str(e)}", "Workspace Creation")
        print(f"Error creating workspace: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def delete_dlits_workspace():
    """Delete DLITS Custom Workspace if it exists"""
    try:
        if frappe.db.exists("Workspace", "DLITS Custom"):
            frappe.delete_doc("Workspace", "DLITS Custom", ignore_permissions=True)
            frappe.db.commit()
            print("Deleted existing workspace")
            return {"success": True, "message": "Workspace deleted"}
        else:
            print("Workspace does not exist")
            return {"success": True, "message": "Workspace does not exist"}
    except Exception as e:
        print(f"Error deleting workspace: {str(e)}")
        return {"success": False, "error": str(e)}