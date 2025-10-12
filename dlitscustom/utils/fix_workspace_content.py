import frappe
import json

@frappe.whitelist()
def fix_workspace_content():
    """Fix the workspace content to show shortcuts properly"""
    
    try:
        # Update the workspace content field with proper JSON structure
        content = [
            {
                "type": "shortcut",
                "data": {
                    "shortcut_name": "Pricing Rule Dlits",
                    "col": 4
                }
            },
            {
                "type": "shortcut",
                "data": {
                    "shortcut_name": "Sales Partner",
                    "col": 4
                }
            },
            {
                "type": "shortcut",
                "data": {
                    "shortcut_name": "Payment Entry",
                    "col": 4
                }
            },
            {
                "type": "shortcut",
                "data": {
                    "shortcut_name": "Sales Order",
                    "col": 4
                }
            },
            {
                "type": "shortcut",
                "data": {
                    "shortcut_name": "Sales Invoice",
                    "col": 4
                }
            },
            {
                "type": "shortcut",
                "data": {
                    "shortcut_name": "Item Price",
                    "col": 4
                }
            }
        ]
        
        # Update the workspace content
        frappe.db.sql("""
            UPDATE `tabWorkspace` 
            SET content = %s 
            WHERE name = 'DLITS Custom'
        """, (json.dumps(content),))
        
        frappe.db.commit()
        
        print("Successfully updated workspace content")
        return {
            "success": True,
            "message": "Workspace content updated. Please refresh your browser to see the shortcuts.",
            "content_items": len(content)
        }
        
    except Exception as e:
        frappe.log_error(f"Error updating workspace content: {str(e)}", "Workspace Content Update")
        print(f"Error updating workspace content: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def check_workspace_content():
    """Check the current workspace content"""
    
    try:
        workspace_data = frappe.db.sql("""
            SELECT name, content, title, label
            FROM `tabWorkspace` 
            WHERE name = 'DLITS Custom'
        """, as_dict=True)
        
        if not workspace_data:
            return {"exists": False, "message": "Workspace not found"}
        
        workspace = workspace_data[0]
        content = workspace.content
        
        print(f"Workspace: {workspace.name}")
        print(f"Title: {workspace.title}")
        print(f"Label: {workspace.label}")
        print(f"Content: {content}")
        
        if content:
            try:
                parsed_content = json.loads(content)
                print(f"Parsed content items: {len(parsed_content)}")
                for i, item in enumerate(parsed_content):
                    print(f"  {i+1}. {item}")
            except:
                print("Content is not valid JSON")
        
        return {
            "exists": True,
            "workspace": workspace,
            "content_length": len(content) if content else 0,
            "message": "Workspace content checked"
        }
        
    except Exception as e:
        print(f"Error checking workspace content: {str(e)}")
        return {"exists": False, "error": str(e)}