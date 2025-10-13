import frappe
import json

def debug_workspace():
    """Debug workspace to see what's actually loaded"""

    print("🔍 Debugging DLITS Custom workspace...")

    try:
        # Check if workspace exists
        if not frappe.db.exists('Workspace', 'DLITS Custom'):
            print("❌ Workspace not found in database")
            return

        workspace = frappe.get_doc('Workspace', 'DLITS Custom')

        print(f"✅ Workspace found: {workspace.name}")
        print(f"   Label: {workspace.label}")
        print(f"   Public: {workspace.public}")
        print(f"   Hidden: {workspace.is_hidden}")

        # Check all links
        print(f"\n📎 Total links: {len(workspace.links)}")
        for i, link in enumerate(workspace.links):
            print(f"   {i+1}. {link.label} ({link.type}) - {'Hidden' if link.hidden else 'Visible'}")

        # Check tools-related links specifically
        print("\n🔧 Tools-related links:")
        tools_links = [link for link in workspace.links if 'Tools' in link.label or link.label in ['Employee Tools Allocation']]
        for link in tools_links:
            print(f"   • {link.label} ({link.link_to}) - {link.type}")

        # Check all shortcuts
        print(f"\n🔗 Total shortcuts: {len(workspace.shortcuts)}")
        for i, shortcut in enumerate(workspace.shortcuts):
            print(f"   {i+1}. {shortcut.label} -> {shortcut.link_to} ({shortcut.type})")

        # Check tools-related shortcuts specifically
        print("\n🔧 Tools-related shortcuts:")
        tools_shortcuts = [shortcut for shortcut in workspace.shortcuts if 'Tools' in shortcut.label or shortcut.label in ['Employee Tools Allocation']]
        for shortcut in tools_shortcuts:
            print(f"   • {shortcut.label} -> {shortcut.link_to}")

        # Check if the DocTypes are accessible
        print("
📋 DocType access check:"        doctypes = ['Tools Transfer Dlits', 'Employee Tools Allocation']
        for doctype in doctypes:
            try:
                if frappe.db.exists('DocType', doctype):
                    dt = frappe.get_doc('DocType', doctype)
                    print(f"   ✅ {doctype}: Module={dt.module}, Is Hidden={dt.is_hidden}")
                else:
                    print(f"   ❌ {doctype}: Not found")
            except Exception as e:
                print(f"   ❌ {doctype}: Error - {str(e)}")

        # Check reports
        print("
📊 Report access check:"        reports = ['Tools Transfer Report']
        for report in reports:
            try:
                if frappe.db.exists('Report', report):
                    rpt = frappe.get_doc('Report', report)
                    print(f"   ✅ {report}: Module={rpt.module}, Is Hidden={rpt.is_hidden}")
                else:
                    print(f"   ❌ {report}: Not found")
            except Exception as e:
                print(f"   ❌ {report}: Error - {str(e)}")

    except Exception as e:
        print(f"❌ Error debugging workspace: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_workspace()