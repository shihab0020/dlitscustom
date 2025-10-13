import frappe

def check_doctype_status():
    """Check if tools-related DocTypes are properly registered"""

    print("🔍 Checking DocType registration status...")

    doctypes_to_check = [
        "Employee Tools Allocation",
        "Tools Transfer Dlits"
    ]

    reports_to_check = [
        "Tools Transfer Report"
    ]

    print("\n📋 DocTypes:")
    for doctype in doctypes_to_check:
        exists = frappe.db.exists('DocType', doctype)
        print(f"   {'✅' if exists else '❌'} {doctype}: {'Registered' if exists else 'Not Found'}")

    print("\n📊 Reports:")
    for report in reports_to_check:
        exists = frappe.db.exists('Report', report)
        print(f"   {'✅' if exists else '❌'} {report}: {'Registered' if exists else 'Not Found'}")

    # Check workspace
    print("\n🏢 Workspace:")
    workspace_exists = frappe.db.exists('Workspace', 'DLITS Custom')
    print(f"   {'✅' if workspace_exists else '❌'} DLITS Custom Workspace: {'Exists' if workspace_exists else 'Not Found'}")

    if workspace_exists:
        # Check workspace links
        workspace = frappe.get_doc('Workspace', 'DLITS Custom')
        tools_links = [link for link in workspace.links if 'Tools' in link.label]

        print(f"   📎 Tools-related links in workspace: {len(tools_links)}")
        for link in tools_links:
            print(f"      • {link.label} ({link.type})")

        # Check shortcuts
        tools_shortcuts = [shortcut for shortcut in workspace.shortcuts if 'Tools' in shortcut.label]
        print(f"   🔗 Tools-related shortcuts in workspace: {len(tools_shortcuts)}")
        for shortcut in tools_shortcuts:
            print(f"      • {shortcut.label}")

    return True

if __name__ == "__main__":
    check_doctype_status()