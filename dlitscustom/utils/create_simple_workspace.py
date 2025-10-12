import frappe
from frappe import _

@frappe.whitelist()
def create_simple_dlits_workspace():
    """Create a simple DLITS Custom Workspace"""
    
    try:
        # Check if workspace already exists
        if frappe.db.exists("Workspace", "DLITS Custom"):
            frappe.delete_doc("Workspace", "DLITS Custom", ignore_permissions=True)
            print("Deleted existing workspace")
        
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
            "module": "dlitscustom"
        })
        
        workspace.insert(ignore_permissions=True)
        
        # Add shortcuts
        shortcuts = [
            {
                "label": "Pricing Rule Dlits",
                "link_to": "Pricing Rule Dlits",
                "type": "DocType",
                "icon": "fa fa-tags",
                "color": "#3498db",
                "description": "Advanced pricing rules with multiple base price types"
            },
            {
                "label": "Sales Partner",
                "link_to": "Sales Partner", 
                "type": "DocType",
                "icon": "fa fa-handshake-o",
                "color": "#e74c3c",
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
                "description": "Sales orders with pricing rules"
            },
            {
                "label": "Sales Invoice",
                "link_to": "Sales Invoice",
                "type": "DocType", 
                "icon": "fa fa-file-text",
                "color": "#27ae60",
                "description": "Sales invoices with commission tracking"
            },
            {
                "label": "Item Price",
                "link_to": "Item Price",
                "type": "DocType", 
                "icon": "fa fa-money",
                "color": "#8e44ad",
                "description": "Standard item pricing"
            }
        ]
        
        for shortcut_data in shortcuts:
            shortcut = frappe.get_doc({
                "doctype": "Workspace Shortcut",
                "parent": workspace.name,
                "parenttype": "Workspace",
                "parentfield": "shortcuts",
                **shortcut_data
            })
            shortcut.insert(ignore_permissions=True)
        
        # Add cards
        cards_data = [
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
                        "label": "Payment Entry",
                        "link_to": "Payment Entry",
                        "link_type": "DocType",
                        "description": "Process commission payments"
                    },
                    {
                        "label": "Supplier",
                        "link_to": "Supplier",
                        "link_type": "DocType",
                        "description": "Linked suppliers for commission payments"
                    }
                ]
            }
        ]
        
        for card_data in cards_data:
            card = frappe.get_doc({
                "doctype": "Workspace Card",
                "parent": workspace.name,
                "parenttype": "Workspace", 
                "parentfield": "cards",
                "label": card_data["label"]
            })
            card.insert(ignore_permissions=True)
            
            for link_data in card_data["links"]:
                link = frappe.get_doc({
                    "doctype": "Workspace Link",
                    "parent": card.name,
                    "parenttype": "Workspace Card",
                    "parentfield": "links",
                    **link_data
                })
                link.insert(ignore_permissions=True)
        
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