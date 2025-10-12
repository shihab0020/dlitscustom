import frappe

def check_reports_and_workspace():
    """Check if reports exist and workspace status"""
    
    print("🔍 Checking DLITS Custom Reports...")
    
    # Check if reports exist
    reports = ['DLITS Customer Ledger Report', 'DLITS Supplier Ledger Report', 'DLITS Tax Report']
    for report in reports:
        exists = frappe.db.exists('Report', report)
        print(f"   Report '{report}': {'✅ exists' if exists else '❌ not found'}")
    
    print("\n🔍 Checking DLITS Custom Workspace...")
    
    # Check workspace
    workspace_name = 'DLITS Custom'
    if frappe.db.exists('Workspace', workspace_name):
        workspace = frappe.get_doc('Workspace', workspace_name)
        print(f"   Workspace found: {workspace.name}")
        print(f"   Number of shortcuts: {len(workspace.shortcuts) if workspace.shortcuts else 0}")
        
        # List all shortcuts
        if workspace.shortcuts:
            print("   Current shortcuts:")
            for i, shortcut in enumerate(workspace.shortcuts, 1):
                print(f"      {i}. {shortcut.label} ({shortcut.type})")
        else:
            print("   No shortcuts found")
            
        return workspace
    else:
        print("   ❌ Workspace not found")
        return None

def add_reports_to_workspace_direct():
    """Add reports directly to workspace"""
    
    try:
        print("\n🔧 Adding reports to DLITS Custom workspace...")
        
        # Get workspace
        workspace_name = 'DLITS Custom'
        workspace = frappe.get_doc('Workspace', workspace_name)
        
        # Reports to add
        reports_to_add = [
            {
                "label": "Customer Ledger Report",
                "name": "DLITS Customer Ledger Report",
                "type": "Report",
                "description": "Customer invoices, payments, and balance analysis",
                "color": "#2e7d32"
            },
            {
                "label": "Supplier Ledger Report", 
                "name": "DLITS Supplier Ledger Report",
                "type": "Report",
                "description": "Supplier invoices, payments, and balance analysis",
                "color": "#dc3545"
            },
            {
                "label": "Tax Report",
                "name": "DLITS Tax Report", 
                "type": "Report",
                "description": "Tax analysis by rates for sales and purchases",
                "color": "#6f42c1"
            }
        ]
        
        # Check and add each report
        added_count = 0
        for report_info in reports_to_add:
            # Check if already exists
            exists = False
            for shortcut in workspace.shortcuts:
                if shortcut.name == report_info["name"] or shortcut.label == report_info["label"]:
                    exists = True
                    break
            
            if not exists:
                # Add the shortcut
                workspace.append("shortcuts", {
                    "label": report_info["label"],
                    "name": report_info["name"],
                    "type": report_info["type"],
                    "description": report_info["description"],
                    "color": report_info["color"]
                })
                print(f"   ✅ Added {report_info['label']}")
                added_count += 1
            else:
                print(f"   ⚠️  {report_info['label']} already exists")
        
        if added_count > 0:
            # Save workspace
            workspace.flags.ignore_validate = True
            workspace.flags.ignore_mandatory = True
            workspace.save(ignore_permissions=True)
            frappe.db.commit()
            print(f"   ✅ Workspace updated with {added_count} new reports")
        else:
            print("   ℹ️  No new reports to add")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        frappe.db.rollback()
        return False

if __name__ == "__main__":
    check_reports_and_workspace()
    add_reports_to_workspace_direct()
    print("\n" + "="*50)
    check_reports_and_workspace()