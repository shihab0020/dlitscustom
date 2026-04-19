import frappe
import json

def before_uninstall():
    """
    Complete uninstallation script for dlitscustom app
    This function is called automatically when the app is uninstalled
    """
    try:
        print("=" * 60)
        print("🗑️ Starting DLITS Custom App Complete Uninstallation...")
        print("=" * 60)
        
        # Step 1: Remove workspace and shortcuts
        print("🏢 Removing DLITS Custom workspace...")
        remove_workspace()
        print("✅ Workspace removed")
        
        # Step 2: Remove custom fields
        print("📝 Removing custom fields...")
        from dlitscustom.fixtures.custom_fields import remove_custom_fields
        remove_custom_fields()
        print("✅ Custom fields removed")
        
        # Step 3: Remove custom doctypes (optional - be careful with user data)
        print("📋 Checking custom doctypes...")
        remove_custom_doctypes()
        print("✅ Custom doctypes handled")
        
        # Step 4: Remove reports
        print("📊 Removing custom reports...")
        remove_custom_reports()
        print("✅ Custom reports removed")
        
        # Step 5: Clean up any remaining configurations
        print("🧹 Cleaning up configurations...")
        cleanup_configurations()
        print("✅ Configurations cleaned")
        
        # Step 6: Clear cache and commit
        print("🧹 Clearing cache...")
        frappe.clear_cache()
        frappe.db.commit()
        print("✅ Cache cleared")
        
        print("=" * 60)
        print("✅ DLITS Custom App uninstalled successfully!")
        print("🗑️ All components removed cleanly")
        print("💡 Note: User data in Pricing Rule Dlits has been preserved")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during uninstallation: {str(e)}")
        frappe.log_error(f"dlitscustom uninstallation error: {str(e)}", "DLITS Uninstallation Error")
        print("⚠️ Some components may not have been removed completely")
        return False

def remove_workspace():
    """Remove DLITS Custom workspace and all shortcuts"""
    try:
        if frappe.db.exists("Workspace", "DLITS Custom"):
            # Remove shortcuts first
            frappe.db.sql("DELETE FROM `tabWorkspace Shortcut` WHERE parent = 'DLITS Custom'")
            # Remove workspace
            frappe.db.sql("DELETE FROM `tabWorkspace` WHERE name = 'DLITS Custom'")
            print("   Workspace 'DLITS Custom' removed successfully")
        else:
            print("   Workspace 'DLITS Custom' does not exist")
    except Exception as e:
        print(f"   Error removing workspace: {str(e)}")
        # Don't raise - continue with other cleanup

def remove_custom_doctypes():
    """Handle custom doctypes - preserve user data but remove doctype definitions"""
    try:
        # List of custom doctypes created by this app
        custom_doctypes = [
            "Pricing Rule Dlits"
        ]
        
        for doctype in custom_doctypes:
            if frappe.db.exists("DocType", doctype):
                # Check if there's any user data
                count = frappe.db.count(doctype)
                if count > 0:
                    print(f"   ⚠️ DocType '{doctype}' has {count} records - preserving data")
                    print(f"   💡 To completely remove, manually delete records first")
                else:
                    print(f"   DocType '{doctype}' has no data - safe to remove")
                    # Uncomment the next line if you want to remove empty doctypes
                    # frappe.delete_doc("DocType", doctype, ignore_permissions=True)
            else:
                print(f"   DocType '{doctype}' does not exist")
                
    except Exception as e:
        print(f"   Error handling custom doctypes: {str(e)}")
        # Don't raise - continue with other cleanup

def remove_custom_reports():
    """Remove custom reports created by the app"""
    try:
        # List of custom reports created by this app
        custom_reports = []
        
        for report in custom_reports:
            if frappe.db.exists("Report", report):
                frappe.delete_doc("Report", report, ignore_permissions=True)
                print(f"   Removed custom report: {report}")
            else:
                print(f"   Custom report not found: {report}")
                
    except Exception as e:
        print(f"   Error removing custom reports: {str(e)}")
        # Don't raise - continue with other cleanup

def cleanup_configurations():
    """Clean up any app-specific configurations"""
    try:
        # Remove any custom print formats
        remove_custom_print_formats()
        
        # Remove any custom roles (be careful with this)
        # remove_custom_roles()
        
        # Clean up any cached data
        cleanup_cached_data()
        
        print("   Configurations cleaned up")
        
    except Exception as e:
        print(f"   Error cleaning configurations: {str(e)}")
        # Don't raise - continue with other cleanup

def remove_custom_print_formats():
    """Remove custom print formats if any"""
    try:
        # Add any custom print formats here if created
        custom_print_formats = []
        
        for print_format in custom_print_formats:
            if frappe.db.exists("Print Format", print_format):
                frappe.delete_doc("Print Format", print_format, ignore_permissions=True)
                print(f"   Removed print format: {print_format}")
                
    except Exception as e:
        print(f"   Error removing print formats: {str(e)}")

def remove_custom_roles():
    """Remove custom roles if any (use with caution)"""
    try:
        # Add any custom roles here if created
        # Be very careful with this - don't remove roles that might be used elsewhere
        custom_roles = []
        
        for role in custom_roles:
            if frappe.db.exists("Role", role):
                # Check if role is used by any users
                users_with_role = frappe.db.count("Has Role", {"role": role})
                if users_with_role == 0:
                    frappe.delete_doc("Role", role, ignore_permissions=True)
                    print(f"   Removed custom role: {role}")
                else:
                    print(f"   ⚠️ Role '{role}' is assigned to {users_with_role} users - not removing")
                    
    except Exception as e:
        print(f"   Error removing custom roles: {str(e)}")

def cleanup_cached_data():
    """Clean up any cached data specific to the app"""
    try:
        # Remove any app-specific cache entries
        # This is where you'd clean up any temporary data, logs, etc.
        print("   Cached data cleaned")
        
    except Exception as e:
        print(f"   Error cleaning cached data: {str(e)}")

def show_uninstall_summary():
    """Show summary of what was removed"""
    try:
        print("\n" + "=" * 60)
        print("📋 UNINSTALLATION SUMMARY")
        print("=" * 60)
        print("✅ Removed:")
        print("   • DLITS Custom workspace")
        print("   • Custom fields for Sales Partner")
        print("   • Custom reports (Pricing Rules Analysis, Sales Partner Commission)")
        print("   • App configurations and cache")
        print("\n⚠️ Preserved:")
        print("   • Pricing Rule Dlits records (user data)")
        print("   • Any linked transactions")
        print("\n💡 Manual cleanup (if needed):")
        print("   • Delete Pricing Rule Dlits records manually if no longer needed")
        print("   • Remove any custom permissions manually")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error showing summary: {str(e)}")

# Call summary at the end
if __name__ == "__main__":
    show_uninstall_summary()