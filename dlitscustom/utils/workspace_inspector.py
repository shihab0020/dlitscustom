import frappe

def inspect_workspace():
    """Inspect the current workspace state"""

    print("🔍 Inspecting DLITS Custom workspace...")

    try:
        # Check workspace
        if not frappe.db.exists('Workspace', 'DLITS Custom'):
            print("❌ Workspace not found")
            return

        workspace = frappe.get_doc('Workspace', 'DLITS Custom')
        print(f"✅ Found workspace: {workspace.name}")

        # Count tools-related items
        tools_links = [link for link in workspace.links if 'Tools' in link.label]
        tools_shortcuts = [shortcut for shortcut in workspace.shortcuts if 'Tools' in shortcut.label]

        print(f"📎 Tools links found: {len(tools_links)}")
        for link in tools_links:
            print(f"   • {link.label}")

        print(f"🔗 Tools shortcuts found: {len(tools_shortcuts)}")
        for shortcut in tools_shortcuts:
            print(f"   • {shortcut.label}")

        # Check specific items
        print("\n🔍 Checking specific items:")
        items_to_check = [
            ('Tools Transfer Dlits', 'DocType'),
            ('Tools Transfer Report', 'Report'),
            ('Employee Tools Allocation', 'DocType')
        ]

        for item_name, item_type in items_to_check:
            if item_type == 'DocType':
                exists = frappe.db.exists('DocType', item_name)
            else:
                exists = frappe.db.exists('Report', item_name)

            print(f"   {'✅' if exists else '❌'} {item_name}: {'Found' if exists else 'Missing'}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    inspect_workspace()