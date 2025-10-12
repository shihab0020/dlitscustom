import frappe

def add_dlits_sales_partner_shortcut():
    """
    Add DLITS Sales Partner shortcut to workspace
    """
    try:
        print("🔧 Adding DLITS Sales Partner shortcut to workspace...")
        
        # Get the workspace
        workspace_name = "DLITS Custom"
        if not frappe.db.exists("Workspace", workspace_name):
            print(f"   ⚠️  Workspace '{workspace_name}' not found")
            return False
            
        workspace = frappe.get_doc("Workspace", workspace_name)
        
        # Check if DLITS Sales Partner shortcut already exists
        dlits_partner_exists = False
        for shortcut in workspace.shortcuts:
            if shortcut.label == "DLITS Sales Partner":
                dlits_partner_exists = True
                print(f"   ✅ DLITS Sales Partner shortcut already exists")
                break
        
        # Add DLITS Sales Partner shortcut if it doesn't exist
        if not dlits_partner_exists:
            workspace.append("shortcuts", {
                "label": "DLITS Sales Partner",
                "name": "DLITS Sales Partner",
                "type": "DocType",
                "description": "Manage sales partners with automatic supplier linking and commission payments",
                "color": "#e74c3c"
            })
            print(f"   ✅ Added DLITS Sales Partner shortcut")
        
        # Save the workspace
        workspace.flags.ignore_validate = True
        workspace.flags.ignore_mandatory = True
        workspace.save(ignore_permissions=True)
        frappe.db.commit()
        
        print("   ✅ Workspace updated successfully")
        print("\n📝 Next Steps:")
        print("   1. Clear browser cache: Ctrl+Shift+R")
        print("   2. Refresh the workspace page")
        print("   3. Check for DLITS Sales Partner shortcut")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        frappe.db.rollback()
        return False

def list_current_shortcuts():
    """
    List all current shortcuts in DLITS Custom workspace
    """
    try:
        print("📋 Current shortcuts in DLITS Custom workspace:")
        
        workspace_name = "DLITS Custom"
        if not frappe.db.exists("Workspace", workspace_name):
            print(f"   ⚠️  Workspace '{workspace_name}' not found")
            return False
            
        workspace = frappe.get_doc("Workspace", workspace_name)
        
        if not workspace.shortcuts:
            print("   📝 No shortcuts found")
            return True
            
        for i, shortcut in enumerate(workspace.shortcuts, 1):
            print(f"   {i}. {shortcut.label} ({shortcut.type})")
            if hasattr(shortcut, 'description') and shortcut.description:
                print(f"      Description: {shortcut.description}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    list_current_shortcuts()
    print("\n" + "="*50)
    add_dlits_sales_partner_shortcut()