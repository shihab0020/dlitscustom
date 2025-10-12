import frappe

def add_custom_reports_shortcuts():
    """
    Add DLITS Custom Reports shortcuts to workspace
    """
    try:
        print("🔧 Adding DLITS Custom Reports shortcuts to workspace...")
        
        # Get the workspace
        workspace_name = "DLITS Custom"
        if not frappe.db.exists("Workspace", workspace_name):
            print(f"   ⚠️  Workspace '{workspace_name}' not found")
            return False
            
        workspace = frappe.get_doc("Workspace", workspace_name)
        
        # Define the reports to add
        reports_to_add = [
            {
                "label": "Customer Ledger Report",
                "name": "DLITS Customer Ledger Report",
                "type": "Report",
                "description": "Customer invoices, payments, and balance analysis with PDF/Excel export",
                "color": "#2e7d32"
            },
            {
                "label": "Supplier Ledger Report", 
                "name": "DLITS Supplier Ledger Report",
                "type": "Report",
                "description": "Supplier invoices, payments, and balance analysis with PDF/Excel export",
                "color": "#dc3545"
            },
            {
                "label": "Tax Report",
                "name": "DLITS Tax Report", 
                "type": "Report",
                "description": "Tax analysis by rates for sales and purchases with PDF/Excel export",
                "color": "#6f42c1"
            }
        ]
        
        # Check and add each report shortcut
        for report_info in reports_to_add:
            report_exists = False
            for shortcut in workspace.shortcuts:
                if shortcut.label == report_info["label"] or shortcut.name == report_info["name"]:
                    report_exists = True
                    print(f"   ✅ {report_info['label']} shortcut already exists")
                    break
            
            # Add report shortcut if it doesn't exist
            if not report_exists:
                workspace.append("shortcuts", {
                    "label": report_info["label"],
                    "name": report_info["name"],
                    "type": report_info["type"],
                    "description": report_info["description"],
                    "color": report_info["color"],
                    "is_query_report": 1
                })
                print(f"   ✅ Added {report_info['label']} shortcut")
        
        # Save the workspace
        workspace.flags.ignore_validate = True
        workspace.flags.ignore_mandatory = True
        workspace.save(ignore_permissions=True)
        frappe.db.commit()
        
        print("   ✅ Workspace updated successfully")
        print("\n📝 Next Steps:")
        print("   1. Clear browser cache: Ctrl+Shift+R")
        print("   2. Refresh the workspace page")
        print("   3. Check for new report shortcuts in DLITS Custom workspace")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        frappe.db.rollback()
        return False

def add_custom_reports_to_cards():
    """
    Add DLITS Custom Reports to workspace cards
    """
    try:
        print("🔧 Adding DLITS Custom Reports to workspace cards...")
        
        # Get the workspace
        workspace_name = "DLITS Custom"
        if not frappe.db.exists("Workspace", workspace_name):
            print(f"   ⚠️  Workspace '{workspace_name}' not found")
            return False
            
        workspace = frappe.get_doc("Workspace", workspace_name)
        
        # Check if Financial Reports card already exists
        financial_reports_card_exists = False
        for card in workspace.cards:
            if card.label == "Financial Reports":
                financial_reports_card_exists = True
                print(f"   ✅ Financial Reports card already exists")
                break
        
        # Add Financial Reports card if it doesn't exist
        if not financial_reports_card_exists:
            workspace.append("cards", {
                "label": "Financial Reports"
            })
            print(f"   ✅ Added Financial Reports card")
            
            # Get the newly added card
            financial_card = workspace.cards[-1]
            
            # Add report items to the card
            reports_to_add = [
                {
                    "type": "report",
                    "name": "DLITS Customer Ledger Report",
                    "label": "Customer Ledger",
                    "description": "Customer invoices, payments, balances, and aging analysis with PDF/Excel export"
                },
                {
                    "type": "report",
                    "name": "DLITS Supplier Ledger Report",
                    "label": "Supplier Ledger", 
                    "description": "Supplier invoices, payments, balances, and outstanding analysis with PDF/Excel export"
                },
                {
                    "type": "report",
                    "name": "DLITS Tax Report",
                    "label": "Tax Analysis",
                    "description": "Tax amounts by rates for sales and purchase transactions with visual breakdown and PDF/Excel export"
                }
            ]
            
            for report_item in reports_to_add:
                financial_card.append("items", report_item)
                print(f"   ✅ Added {report_item['label']} to Financial Reports card")
        
        # Save the workspace
        workspace.flags.ignore_validate = True
        workspace.flags.ignore_mandatory = True
        workspace.save(ignore_permissions=True)
        frappe.db.commit()
        
        print("   ✅ Workspace cards updated successfully")
        
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

def list_current_cards():
    """
    List all current cards in DLITS Custom workspace
    """
    try:
        print("📋 Current cards in DLITS Custom workspace:")
        
        workspace_name = "DLITS Custom"
        if not frappe.db.exists("Workspace", workspace_name):
            print(f"   ⚠️  Workspace '{workspace_name}' not found")
            return False
            
        workspace = frappe.get_doc("Workspace", workspace_name)
        
        if not workspace.cards:
            print("   📝 No cards found")
            return True
            
        for i, card in enumerate(workspace.cards, 1):
            print(f"   {i}. {card.label}")
            if hasattr(card, 'items') and card.items:
                for j, item in enumerate(card.items, 1):
                    print(f"      {j}. {item.label} ({item.type})")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("DLITS Custom Reports Workspace Integration")
    print("="*60)
    
    list_current_shortcuts()
    print("\n" + "="*50)
    list_current_cards()
    print("\n" + "="*50)
    add_custom_reports_shortcuts()
    print("\n" + "="*50)
    add_custom_reports_to_cards()
    print("\n" + "="*60)