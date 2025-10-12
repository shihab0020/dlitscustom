import frappe

def refresh_dlits_workspace():
    """
    Refresh DLITS Custom workspace to ensure proper navigation
    """
    try:
        print("🔄 Refreshing DLITS Custom workspace...")
        
        # Clear workspace cache
        frappe.cache().delete_key("workspace_sidebar")
        frappe.cache().delete_key("workspace_*")
        
        # Check if workspace exists
        workspace_name = "DLITS Custom"
        if frappe.db.exists("Workspace", workspace_name):
            workspace = frappe.get_doc("Workspace", workspace_name)
            
            # Update shortcuts to ensure DLITS Sales Partner is used
            for shortcut in workspace.shortcuts:
                if shortcut.label == "Sales Partner" or (shortcut.label == "DLITS Sales Partner" and shortcut.link_to == "List/DLITS Sales Partner/List"):
                    shortcut.label = "DLITS Sales Partner"
                    shortcut.link_to = "DLITS Sales Partner"
                    shortcut.type = "DocType"
                    print(f"   Updated shortcut: {shortcut.label}")
            
            # Save the workspace
            workspace.save(ignore_permissions=True)
            frappe.db.commit()
            print("   ✅ Workspace updated successfully")
            
        else:
            print("   ⚠️  DLITS Custom workspace not found")
            
        # Clear browser cache instructions
        print("\n📝 Next Steps:")
        print("   1. Clear browser cache (Ctrl+Shift+R)")
        print("   2. Restart Frappe server: bench restart")
        print("   3. Check workspace navigation")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error refreshing workspace: {str(e)}")
        return False

def fix_workspace_shortcuts():
    """
    Fix any remaining Sales Partner shortcuts in workspace
    """
    try:
        print("🔧 Fixing workspace shortcuts...")
        
        # Get all workspaces
        workspaces = frappe.get_all("Workspace", fields=["name"])
        
        for ws in workspaces:
            workspace = frappe.get_doc("Workspace", ws.name)
            updated = False
            
            # Check shortcuts
            for shortcut in workspace.shortcuts:
                if shortcut.label == "Sales Partner" or (shortcut.label == "DLITS Sales Partner" and shortcut.link_to != "DLITS Sales Partner"):
                    shortcut.label = "DLITS Sales Partner"
                    shortcut.link_to = "DLITS Sales Partner"
                    shortcut.type = "DocType"
                    updated = True
                    print(f"   Fixed shortcut in workspace: {ws.name}")
            
            # Check cards
            for card in workspace.cards:
                for item in card.links:
                    if item.label == "Sales Partner" or (item.label == "DLITS Sales Partner" and item.link_to != "DLITS Sales Partner"):
                        item.label = "DLITS Sales Partner"
                        item.link_to = "DLITS Sales Partner"
                        item.type = "doctype"
                        updated = True
                        print(f"   Fixed card item in workspace: {ws.name}")
            
            if updated:
                workspace.save(ignore_permissions=True)
        
        frappe.db.commit()
        print("   ✅ All workspace shortcuts fixed")
        return True
        
    except Exception as e:
        print(f"   ❌ Error fixing shortcuts: {str(e)}")
        return False

if __name__ == "__main__":
    refresh_dlits_workspace()
    fix_workspace_shortcuts()