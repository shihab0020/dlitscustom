import frappe
import json
import os

def rebuild_workspace():
    """Rebuild the DLITS Custom workspace from scratch"""

    print("🔄 Rebuilding DLITS Custom workspace from scratch...")

    try:
        # Delete existing workspace if it exists
        if frappe.db.exists('Workspace', 'DLITS Custom'):
            print("   🗑️ Deleting existing workspace...")
            frappe.delete_doc('Workspace', 'DLITS Custom', ignore_permissions=True, force=True)
            print("   ✅ Existing workspace deleted")

        # Load workspace from JSON file
        workspace_path = os.path.join(
            frappe.get_app_path('dlitscustom'),
            'workspace',
            'dlits_custom',
            'dlits_custom.json'
        )

        if os.path.exists(workspace_path):
            print("   📁 Loading workspace from JSON file...")
            with open(workspace_path, 'r') as f:
                workspace_data = json.load(f)

            # Create workspace document
            workspace_doc = frappe.get_doc(workspace_data)
            workspace_doc.insert(ignore_permissions=True)
            print("   ✅ Workspace created from JSON file")
        else:
            print("   ❌ Workspace JSON file not found, creating basic workspace...")
            create_basic_workspace()

        # Clear cache
        frappe.clear_cache()
        print("   ✅ Cache cleared")

        print("   🎉 Workspace rebuilt successfully!")
        print("\n📝 Next Steps:")
        print("   1. Restart Frappe: bench restart")
        print("   2. Clear browser cache: Ctrl+Shift+R")
        print("   3. Check DLITS Custom workspace")
        print("   4. Tools Management section should now show all 3 items")

        return True

    except Exception as e:
        print(f"❌ Error rebuilding workspace: {str(e)}")
        frappe.log_error(f"Workspace rebuild error: {str(e)}", "Workspace Rebuild")
        return False

def create_basic_workspace():
    """Create a basic workspace if JSON file is not available"""

    print("   📝 Creating basic workspace structure...")

    workspace_doc = frappe.get_doc({
        'doctype': 'Workspace',
        'name': 'DLITS Custom',
        'label': 'DLITS Custom',
        'title': 'DLITS Custom',
        'module': 'dlitscustom',
        'icon': 'fa fa-cogs',
        'indicator_color': 'orange',
        'is_hidden': 0,
        'public': 1,
        'content': json.dumps([{
            'id': 'header_1',
            'type': 'header',
            'data': {'text': '<span class="h4">DLITS Custom</span>', 'col': 12}
        }, {
            'id': 'header_2',
            'type': 'header',
            'data': {'text': '<span class="h4"><b>Pricing & Commission Management</b></span>', 'col': 12}
        }, {
            'id': 'shortcut_1',
            'type': 'shortcut',
            'data': {'shortcut_name': 'Pricing Rule Dlits', 'col': 3}
        }, {
            'id': 'shortcut_2',
            'type': 'shortcut',
            'data': {'shortcut_name': 'DLITS Sales Partner', 'col': 3}
        }, {
            'id': 'shortcut_3',
            'type': 'shortcut',
            'data': {'shortcut_name': 'Commission Report', 'col': 3}
        }, {
            'id': 'header_3',
            'type': 'header',
            'data': {'text': '<span class="h4"><b>Tools Management</b></span>', 'col': 12}
        }, {
            'id': 'shortcut_7',
            'type': 'shortcut',
            'data': {'shortcut_name': 'Tools Transfer', 'col': 4}
        }, {
            'id': 'shortcut_8',
            'type': 'shortcut',
            'data': {'shortcut_name': 'Tools Transfer Report', 'col': 4}
        }, {
            'id': 'shortcut_9',
            'type': 'shortcut',
            'data': {'shortcut_name': 'Employee Tools Allocation', 'col': 4}
        }, {
            'id': 'header_4',
            'type': 'header',
            'data': {'text': '<span class="h4"><b>Financial Reports</b></span>', 'col': 12}
        }, {
            'id': 'shortcut_4',
            'type': 'shortcut',
            'data': {'shortcut_name': 'Customer Ledger Report', 'col': 4}
        }, {
            'id': 'shortcut_5',
            'type': 'shortcut',
            'data': {'shortcut_name': 'Supplier Ledger Report', 'col': 4}
        }, {
            'id': 'shortcut_6',
            'type': 'shortcut',
            'data': {'shortcut_name': 'Tax Report', 'col': 4}
        }]),
        'shortcuts': [
            {
                'label': 'Pricing Rule Dlits',
                'link_to': 'Pricing Rule Dlits',
                'type': 'DocType',
                'color': '#3498db'
            },
            {
                'label': 'DLITS Sales Partner',
                'link_to': 'DLITS Sales Partner',
                'type': 'DocType',
                'color': '#e74c3c'
            },
            {
                'label': 'Tools Transfer',
                'link_to': 'Tools Transfer Dlits',
                'type': 'DocType',
                'color': '#28a745'
            },
            {
                'label': 'Tools Transfer Report',
                'link_to': 'Tools Transfer Report',
                'type': 'Report',
                'color': '#17a2b8'
            },
            {
                'label': 'Employee Tools Allocation',
                'link_to': 'Employee Tools Allocation',
                'type': 'DocType',
                'color': '#fd7e14'
            }
        ]
    })

    workspace_doc.insert(ignore_permissions=True)
    print("   ✅ Basic workspace created")

if __name__ == "__main__":
    rebuild_workspace()