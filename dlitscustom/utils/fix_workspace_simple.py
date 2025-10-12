import frappe

def fix_workspace_navigation():
    """
    Simple fix for workspace navigation issues
    """
    try:
        print("🔧 Fixing DLITS Custom workspace navigation...")
        
        # Clear all workspace caches
        frappe.cache().delete_keys("workspace")
        frappe.clear_cache()
        
        # Get the workspace
        workspace_name = "DLITS Custom"
        if not frappe.db.exists("Workspace", workspace_name):
            print(f"   ⚠️  Workspace '{workspace_name}' not found")
            return False
            
        workspace = frappe.get_doc("Workspace", workspace_name)
        
        # Fix shortcuts - remove problematic link_to fields
        for shortcut in workspace.shortcuts:
            if shortcut.label in ["Sales Partner", "DLITS Sales Partner"]:
                shortcut.label = "DLITS Sales Partner"
                shortcut.name = "DLITS Sales Partner"
                shortcut.type = "DocType"
                # Remove the problematic link_to field
                if hasattr(shortcut, 'link_to'):
                    shortcut.link_to = None
                print(f"   ✅ Fixed shortcut: {shortcut.label}")
        
        # Save without validation to avoid link issues
        workspace.flags.ignore_validate = True
        workspace.flags.ignore_mandatory = True
        workspace.save(ignore_permissions=True)
        frappe.db.commit()
        
        print("   ✅ Workspace fixed successfully")
        print("\n📝 Next Steps:")
        print("   1. Restart Frappe: bench restart")
        print("   2. Clear browser cache: Ctrl+Shift+R")
        print("   3. Test navigation in workspace")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        frappe.db.rollback()
        return False

def recreate_workspace():
    """
    Recreate the workspace from scratch if needed
    """
    try:
        print("🔄 Recreating DLITS Custom workspace...")
        
        # Delete existing workspace
        workspace_name = "DLITS Custom"
        if frappe.db.exists("Workspace", workspace_name):
            frappe.delete_doc("Workspace", workspace_name, ignore_permissions=True)
            print("   🗑️  Deleted existing workspace")
        
        # Import workspace from config
        from dlitscustom.install import create_workspace
        create_workspace()
        
        frappe.db.commit()
        print("   ✅ Workspace recreated successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Error recreating workspace: {str(e)}")
        frappe.db.rollback()
        return False

if __name__ == "__main__":
    # Try simple fix first
    if not fix_workspace_navigation():
        print("\n🔄 Simple fix failed, trying to recreate workspace...")
        recreate_workspace()