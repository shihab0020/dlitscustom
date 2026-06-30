import frappe
from frappe import _
import json

def after_install():
    """
    Post-installation setup for dlitscustom app
    """
    try:
        print("=" * 60)
        print("🚀 Starting DLITS Custom App Installation...")
        print("=" * 60)
        
        # Step 1: Create custom fields
        print("📝 Creating custom fields...")
        from dlitscustom.fixtures.custom_fields import create_all_custom_fields
        create_all_custom_fields()
        print("✅ Custom fields created successfully")
        
        # Step 2: Create custom roles
        print("🔑 Creating custom roles...")
        create_custom_roles()
        print("✅ Custom roles created")

        # Step 2b: Create property setters (must survive core upgrades)
        print("🔧 Creating property setters...")
        create_property_setters()
        print("✅ Property setters created")

        # Step 3: Create workspace
        print("🏢 Creating DLITS Custom workspace...")
        create_workspace()
        print("✅ Workspace created successfully")
        
        # Step 3: Create default supplier group
        print("👥 Setting up supplier groups...")
        create_default_supplier_group()
        print("✅ Supplier groups configured")
        
        # Step 4: Set up default settings
        print("⚙️ Configuring default settings...")
        setup_default_settings()
        print("✅ Default settings configured")
        
        # Step 5: Clear cache to ensure changes are reflected
        print("🧹 Clearing cache...")
        frappe.clear_cache()
        frappe.db.commit()
        print("✅ Cache cleared")
        
        print("=" * 60)
        print("🎉 DLITS Custom App installed successfully!")
        print("📋 Features installed:")
        print("   • Advanced Pricing Rules with 4 base price types")
        print("   • Tax Report (sales & purchase tax analysis)")
        print("   • Sales Analytics Report")
        print("   • Customer Followup Management")
        print("=" * 60)
        print("📝 Next Steps:")
        print("   1. Access DLITS Custom workspace to view all features")
        print("   2. Test custom reports with PDF/Excel export functionality")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during installation: {str(e)}")
        frappe.log_error(f"dlitscustom installation error: {str(e)}", "DLITS Installation Error")
        return False

def before_uninstall():
    """
    Pre-uninstallation cleanup for dlitscustom app
    """
    try:
        print("=" * 60)
        print("🗑️ Starting DLITS Custom App Uninstallation...")
        print("=" * 60)
        
        # Step 1: Remove workspace
        print("🏢 Removing DLITS Custom workspace...")
        remove_workspace()
        print("✅ Workspace removed")
        
        # Step 2: Remove custom fields
        print("📝 Removing custom fields...")
        from dlitscustom.fixtures.custom_fields import remove_custom_fields
        remove_custom_fields()
        print("✅ Custom fields removed")
        
        # Step 3: Clean up any remaining data
        print("🧹 Cleaning up remaining data...")
        cleanup_app_data()
        print("✅ Data cleanup completed")
        
        # Step 4: Clear cache
        print("🧹 Clearing cache...")
        frappe.clear_cache()
        frappe.db.commit()
        print("✅ Cache cleared")
        
        print("=" * 60)
        print("✅ DLITS Custom App uninstalled successfully!")
        print("🗑️ All components removed cleanly")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during uninstallation: {str(e)}")
        frappe.log_error(f"dlitscustom uninstallation error: {str(e)}", "DLITS Uninstallation Error")
        return False

def migrate():
    """
    Migration script for dlitscustom app updates
    """
    try:
        print("=" * 60)
        print("🔄 Running DLITS Custom App Migration...")
        print("=" * 60)
        
        # Step 0: Ensure custom roles and property setters exist
        print("🔑 Ensuring custom roles...")
        create_custom_roles()
        print("✅ Custom roles verified")

        print("🔧 Ensuring property setters...")
        create_property_setters()
        print("✅ Property setters verified")

        # Step 1: Update custom fields
        print("📝 Updating custom fields...")
        from dlitscustom.fixtures.custom_fields import create_all_custom_fields
        create_all_custom_fields()
        print("✅ Custom fields updated")
        
        # Step 2: Update workspace
        print("🏢 Updating workspace...")
        update_workspace()
        print("✅ Workspace updated")
        
        # Step 3: Run any pending patches
        print("🔧 Running patches...")
        run_patches()
        print("✅ Patches completed")
        
        # Step 4: Clear cache
        print("🧹 Clearing cache...")
        frappe.clear_cache()
        frappe.db.commit()
        print("✅ Cache cleared")
        
        print("=" * 60)
        print("✅ DLITS Custom App migration completed successfully!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        frappe.log_error(f"dlitscustom migration error: {str(e)}", "DLITS Migration Error")
        return False

def create_custom_roles():
    """Create DLITS custom roles if they do not already exist."""
    roles = [
        {"role_name": "Shb Commission Approver", "desk_access": 1},
        {"role_name": "Shb Allow Below Price",    "desk_access": 1},
    ]
    for role_def in roles:
        if not frappe.db.exists("Role", role_def["role_name"]):
            frappe.get_doc({"doctype": "Role", **role_def}).insert(ignore_permissions=True)
            print(f"   Created role: {role_def['role_name']}")
        else:
            print(f"   Role already exists: {role_def['role_name']}")


def create_property_setters():
    """Recreate all property setters that override core Frappe/ERPNext field properties.
    Must survive upgrades — never modify core JSON files directly."""
    setters = [
        # Contact: make Mobile No editable (core file had read_only=1)
        {
            "doctype_or_field": "DocField",
            "doc_type":    "Contact",
            "field_name":  "mobile_no",
            "property":    "read_only",
            "property_type": "Check",
            "value":       "0",
        },
    ]
    for s in setters:
        existing = frappe.db.get_value(
            "Property Setter",
            {"doc_type": s["doc_type"], "field_name": s.get("field_name"), "property": s["property"]},
            "name"
        )
        if existing:
            frappe.db.set_value("Property Setter", existing, "value", s["value"])
            print(f"   Updated Property Setter: {s['doc_type']}.{s.get('field_name')} → {s['property']} = {s['value']}")
        else:
            frappe.get_doc({"doctype": "Property Setter", **s}).insert(ignore_permissions=True)
            print(f"   Created Property Setter: {s['doc_type']}.{s.get('field_name')} → {s['property']} = {s['value']}")


def create_workspace():
    """Create DLITS Custom workspace from JSON file"""
    try:
        # Check if workspace already exists
        if frappe.db.exists("Workspace", "DLITS Custom"):
            print("   Workspace already exists, updating...")
            update_workspace()
            return
        
        # Load workspace from JSON file
        import os
        workspace_path = os.path.join(
            frappe.get_app_path("dlitscustom"),
            "workspace",
            "dlits_custom",
            "dlits_custom.json"
        )
        
        if os.path.exists(workspace_path):
            with open(workspace_path, 'r') as f:
                workspace_data = json.load(f)
            
            # Create workspace document
            workspace_doc = frappe.get_doc(workspace_data)
            workspace_doc.insert(ignore_permissions=True)
            print("   Workspace created from JSON file")
        else:
            print("   Warning: Workspace JSON file not found, creating basic workspace")
            create_basic_workspace()
        
        # Ensure custom reports are available
        ensure_custom_reports()
        
    except Exception as e:
        print(f"   Error creating workspace: {str(e)}")
        # Fallback to basic workspace creation
        try:
            create_basic_workspace()
        except:
            pass
        raise

def create_basic_workspace():
    """Create basic workspace if JSON file is not available"""
    workspace_doc = frappe.get_doc({
        "doctype": "Workspace",
        "name": "DLITS Custom",
        "label": "DLITS Custom",
        "title": "DLITS Custom",
        "module": "dlitscustom",
        "icon": "fa fa-cogs",
        "indicator_color": "orange",
        "is_hidden": 0,
        "public": 1,
        "shortcuts": [
            {
                "label": "Pricing Rule Dlits",
                "link_to": "Pricing Rule Dlits",
                "type": "DocType",
                "color": "#3498db"
            },
            {
                "label": "Tax Report",
                "link_to": "DLITS Tax Report",
                "type": "Report",
                "color": "#6f42c1"
            }
        ]
    })
    workspace_doc.insert(ignore_permissions=True)

def ensure_custom_reports():
    """Ensure all custom reports are properly registered"""
    reports = [
        "DLITS Tax Report",
        "DLITS Sales Analytics"
    ]

    for report_name in reports:
        if frappe.db.exists("Report", report_name):
            print(f"   ✅ Report '{report_name}' is available")
        else:
            print(f"   ⚠️  Report '{report_name}' not found - may need to restart server")

def update_workspace():
    """Update existing workspace with latest configuration"""
    try:
        # Remove existing workspace
        if frappe.db.exists("Workspace", "DLITS Custom"):
            remove_workspace()
        
        # Recreate workspace with latest configuration
        create_workspace()
        print("   Workspace updated successfully")
        
    except Exception as e:
        print(f"   Error updating workspace: {str(e)}")
        raise

def remove_workspace():
    """Remove DLITS Custom workspace and related data"""
    try:
        if frappe.db.exists("Workspace", "DLITS Custom"):
            # Remove workspace document (this will cascade to child tables)
            frappe.delete_doc("Workspace", "DLITS Custom", ignore_permissions=True)
            print("   Workspace removed successfully")
        else:
            print("   Workspace does not exist")
    except Exception as e:
        print(f"   Error removing workspace: {str(e)}")
        # Fallback to direct SQL deletion
        try:
            frappe.db.sql("DELETE FROM `tabWorkspace Shortcut` WHERE parent = 'DLITS Custom'")
            frappe.db.sql("DELETE FROM `tabWorkspace Link` WHERE parent = 'DLITS Custom'")
            frappe.db.sql("DELETE FROM `tabWorkspace` WHERE name = 'DLITS Custom'")
            print("   Workspace removed using fallback method")
        except:
            pass

def create_default_supplier_group():
    """Create default supplier group for sales partners"""
    try:
        if not frappe.db.exists("Supplier Group", "Sales Partners"):
            supplier_group = frappe.get_doc({
                "doctype": "Supplier Group",
                "supplier_group_name": "Sales Partners",
                "parent_supplier_group": frappe.db.get_single_value("Buying Settings", "supplier_group") or "All Supplier Groups"
            })
            supplier_group.insert(ignore_permissions=True)
            print("   Created 'Sales Partners' supplier group")
        else:
            print("   'Sales Partners' supplier group already exists")
    except Exception as e:
        print(f"   Error creating supplier group: {str(e)}")
        # Don't raise - this is not critical

def setup_default_settings():
    """Set up default settings for the app"""
    try:
        # Any default settings can be configured here
        print("   Default settings configured")
    except Exception as e:
        print(f"   Error setting up defaults: {str(e)}")
        # Don't raise - this is not critical

def cleanup_app_data():
    """Clean up app-specific data during uninstallation"""
    try:
        # Remove custom reports (optional - user may want to keep data)
        reports_to_remove = [
            "DLITS Tax Report",
            "DLITS Sales Analytics"
        ]
        
        for report_name in reports_to_remove:
            if frappe.db.exists("Report", report_name):
                try:
                    frappe.delete_doc("Report", report_name, ignore_permissions=True)
                    print(f"   Removed report: {report_name}")
                except:
                    print(f"   Could not remove report: {report_name}")
        
        # Note: We don't remove user data like DLITS Sales Partner records
        # as they may contain important business data
        print("   App data cleanup completed")
        
    except Exception as e:
        print(f"   Error cleaning up data: {str(e)}")
        # Don't raise - this is not critical

def run_patches():
    """Run any pending patches"""
    try:
        # Run any specific patches needed for migration
        print("   Patches executed")
    except Exception as e:
        print(f"   Error running patches: {str(e)}")
        # Don't raise - this is not critical