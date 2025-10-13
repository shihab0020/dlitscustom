import frappe
import json

def fix_tools_management_workspace():
    """
    Fix the DLITS Custom workspace to include missing Employee Tools Allocation
    """
    try:
        print("🔧 Fixing Tools Management in DLITS Custom workspace...")

        # Check if workspace exists
        if not frappe.db.exists("Workspace", "DLITS Custom"):
            print("   ❌ Workspace 'DLITS Custom' not found")
            return False

        workspace = frappe.get_doc("Workspace", "DLITS Custom")

        # Check if Employee Tools Allocation link already exists
        employee_tools_exists = False
        for link in workspace.links:
            if link.label == "Employee Tools Allocation":
                employee_tools_exists = True
                break

        if not employee_tools_exists:
            # Add Employee Tools Allocation link
            new_link = {
                "hidden": 0,
                "is_query_report": 0,
                "label": "Employee Tools Allocation",
                "link_count": 0,
                "link_to": "Employee Tools Allocation",
                "link_type": "DocType",
                "onboard": 0,
                "type": "Link"
            }
            workspace.append("links", new_link)
            print("   ✅ Added Employee Tools Allocation link")

        # Check if Employee Tools Allocation shortcut already exists
        employee_shortcut_exists = False
        for shortcut in workspace.shortcuts:
            if shortcut.label == "Employee Tools Allocation":
                employee_shortcut_exists = True
                break

        if not employee_shortcut_exists:
            # Add Employee Tools Allocation shortcut
            new_shortcut = {
                "color": "#fd7e14",
                "doc_view": "List",
                "label": "Employee Tools Allocation",
                "link_to": "Employee Tools Allocation",
                "type": "DocType"
            }
            workspace.append("shortcuts", new_shortcut)
            print("   ✅ Added Employee Tools Allocation shortcut")

        # Update the Tools Management card link_count
        for link in workspace.links:
            if link.label == "Tools Management" and link.type == "Card Break":
                link.link_count = 3
                print("   ✅ Updated Tools Management link count to 3")
                break

        # Save the workspace
        workspace.save(ignore_permissions=True)
        frappe.db.commit()

        print("   ✅ Tools Management workspace fixed successfully")
        print("\n📝 Next Steps:")
        print("   1. Restart Frappe: bench restart")
        print("   2. Clear browser cache: Ctrl+Shift+R")
        print("   3. Check DLITS Custom workspace - Tools Management section")
        print("   4. You should now see 'Employee Tools Allocation' in the Tools Management section")

        return True

    except Exception as e:
        print(f"   ❌ Error fixing workspace: {str(e)}")
        frappe.db.rollback()
        return False

if __name__ == "__main__":
    fix_tools_management_workspace()