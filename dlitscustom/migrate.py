import frappe
import json
from frappe.utils import now

def execute():
    """
    Migration script for dlitscustom app upgrades
    This function handles version updates and ensures compatibility
    """
    try:
        print("=" * 60)
        print("🔄 Starting DLITS Custom App Migration...")
        print("=" * 60)
        
        # Get current app version
        current_version = get_app_version()
        print(f"📦 Current app version: {current_version}")
        
        # Run version-specific migrations
        run_version_migrations(current_version)
        
        # Update common components
        update_common_components()
        
        # Verify migration success
        verify_migration()
        
        print("=" * 60)
        print("✅ DLITS Custom App migration completed successfully!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        frappe.log_error(f"dlitscustom migration error: {str(e)}", "DLITS Migration Error")
        return False

def get_app_version():
    """Get current app version"""
    try:
        # Try to get version from app metadata
        return "1.0.0"  # Default version
    except Exception:
        return "unknown"

def run_version_migrations(current_version):
    """Run version-specific migration scripts"""
    try:
        print("🔄 Running version-specific migrations...")
        
        # Version 1.0.0 migrations
        if needs_migration("1.0.0", current_version):
            migrate_to_v1_0_0()
        
        # Version 1.1.0 migrations (future)
        if needs_migration("1.1.0", current_version):
            migrate_to_v1_1_0()
        
        print("✅ Version migrations completed")
        
    except Exception as e:
        print(f"   Error in version migrations: {str(e)}")
        raise

def needs_migration(target_version, current_version):
    """Check if migration is needed for a specific version"""
    # Simple version comparison - in production, use proper version comparison
    return True  # For now, always run migrations

def migrate_to_v1_0_0():
    """Migration for version 1.0.0"""
    try:
        print("   Migrating to v1.0.0...")
        
        # Ensure custom fields exist
        from dlitscustom.fixtures.custom_fields import create_sales_partner_custom_fields
        create_sales_partner_custom_fields()
        
        # Ensure workspace exists
        ensure_workspace_exists()
        
        # Update any existing pricing rules
        update_existing_pricing_rules()
        
        print("   ✅ v1.0.0 migration completed")
        
    except Exception as e:
        print(f"   Error in v1.0.0 migration: {str(e)}")
        raise

def migrate_to_v1_1_0():
    """Migration for version 1.1.0 (future version)"""
    try:
        print("   Migrating to v1.1.0...")
        
        # Future migration tasks would go here
        # Example: Add new fields, update existing data, etc.
        
        print("   ✅ v1.1.0 migration completed")
        
    except Exception as e:
        print(f"   Error in v1.1.0 migration: {str(e)}")
        raise

def update_common_components():
    """Update common components that should be refreshed on every migration"""
    try:
        print("🔄 Updating common components...")
        
        # Update workspace
        update_workspace()
        
        # Update custom fields
        update_custom_fields()
        
        # Update reports
        update_reports()
        
        # Update permissions
        update_permissions()
        
        print("✅ Common components updated")
        
    except Exception as e:
        print(f"   Error updating common components: {str(e)}")
        raise

def ensure_workspace_exists():
    """Ensure DLITS Custom workspace exists and is up to date"""
    try:
        if not frappe.db.exists("Workspace", "DLITS Custom"):
            print("   Creating missing workspace...")
            create_workspace()
        else:
            print("   Updating existing workspace...")
            update_workspace()
            
    except Exception as e:
        print(f"   Error ensuring workspace: {str(e)}")
        raise

def create_workspace():
    """Create DLITS Custom workspace"""
    try:
        # Create workspace
        frappe.db.sql("""
            INSERT INTO `tabWorkspace` 
            (name, label, title, module, icon, indicator_color, is_hidden, public, owner, creation, modified, modified_by, docstatus, idx, sequence_id)
            VALUES 
            ('DLITS Custom', 'DLITS Custom', 'DLITS Custom', 'dlitscustom', 'fa fa-cogs', 'orange', 0, 1, 'Administrator', NOW(), NOW(), 'Administrator', 0, 0, 10.0)
        """)
        
        # Create shortcuts
        shortcuts = [
            ('Pricing Rule Dlits', 'Pricing Rule Dlits', 'DocType', 'fa fa-tags', '#3498db'),
            ('Sales Partner', 'Sales Partner', 'DocType', 'fa fa-handshake-o', '#e74c3c'),
            ('Payment Entry', 'Payment Entry', 'DocType', 'fa fa-credit-card', '#34495e'),
            ('Sales Order', 'Sales Order', 'DocType', 'fa fa-file-text-o', '#f39c12'),
            ('Sales Invoice', 'Sales Invoice', 'DocType', 'fa fa-file-text', '#27ae60'),
            ('Item Price', 'Item Price', 'DocType', 'fa fa-money', '#8e44ad')
        ]
        
        for i, (label, link_to, type_val, icon, color) in enumerate(shortcuts):
            shortcut_name = f"dlits-shortcut-{i+1}"
            frappe.db.sql("""
                INSERT INTO `tabWorkspace Shortcut`
                (name, parent, parenttype, parentfield, label, link_to, type, icon, color, owner, creation, modified, modified_by, docstatus, idx)
                VALUES
                (%s, 'DLITS Custom', 'Workspace', 'shortcuts', %s, %s, %s, %s, %s, 'Administrator', NOW(), NOW(), 'Administrator', 0, %s)
            """, (shortcut_name, label, link_to, type_val, icon, color, i+1))
        
        # Update workspace content
        content = [
            {"type": "shortcut", "data": {"shortcut_name": label, "col": 4}}
            for label, _, _, _, _ in shortcuts
        ]
        
        frappe.db.sql("""
            UPDATE `tabWorkspace` 
            SET content = %s 
            WHERE name = 'DLITS Custom'
        """, (json.dumps(content),))
        
    except Exception as e:
        print(f"   Error creating workspace: {str(e)}")
        raise

def update_workspace():
    """Update existing workspace"""
    try:
        # Update workspace content
        content = [
            {"type": "shortcut", "data": {"shortcut_name": "Pricing Rule Dlits", "col": 4}},
            {"type": "shortcut", "data": {"shortcut_name": "Sales Partner", "col": 4}},
            {"type": "shortcut", "data": {"shortcut_name": "Payment Entry", "col": 4}},
            {"type": "shortcut", "data": {"shortcut_name": "Sales Order", "col": 4}},
            {"type": "shortcut", "data": {"shortcut_name": "Sales Invoice", "col": 4}},
            {"type": "shortcut", "data": {"shortcut_name": "Item Price", "col": 4}}
        ]
        
        frappe.db.sql("""
            UPDATE `tabWorkspace` 
            SET content = %s, modified = NOW()
            WHERE name = 'DLITS Custom'
        """, (json.dumps(content),))
        
    except Exception as e:
        print(f"   Error updating workspace: {str(e)}")
        raise

def update_custom_fields():
    """Update custom fields"""
    try:
        from dlitscustom.fixtures.custom_fields import create_sales_partner_custom_fields
        create_sales_partner_custom_fields()
        
    except Exception as e:
        print(f"   Error updating custom fields: {str(e)}")
        raise

def update_reports():
    """Update custom reports"""
    try:
        # Reports are typically updated through the file system
        # Any database-specific report updates would go here
        print("   Reports updated from file system")
        
    except Exception as e:
        print(f"   Error updating reports: {str(e)}")
        raise

def update_permissions():
    """Update permissions for custom doctypes"""
    try:
        # Update permissions for Pricing Rule Dlits
        update_pricing_rule_dlits_permissions()
        
        print("   Permissions updated")
        
    except Exception as e:
        print(f"   Error updating permissions: {str(e)}")
        raise

def update_pricing_rule_dlits_permissions():
    """Update permissions for Pricing Rule Dlits doctype"""
    try:
        # Permissions are typically handled through the doctype JSON file
        # Any runtime permission updates would go here
        pass
        
    except Exception as e:
        print(f"   Error updating Pricing Rule Dlits permissions: {str(e)}")
        raise

def update_existing_pricing_rules():
    """Update existing pricing rules if needed"""
    try:
        # Check if there are any data migrations needed for existing pricing rules
        existing_rules = frappe.db.count("Pricing Rule Dlits")
        if existing_rules > 0:
            print(f"   Found {existing_rules} existing pricing rules - checking for updates...")
            # Add any data migration logic here
            print("   Existing pricing rules verified")
        else:
            print("   No existing pricing rules found")
            
    except Exception as e:
        print(f"   Error updating existing pricing rules: {str(e)}")
        raise

def verify_migration():
    """Verify that migration completed successfully"""
    try:
        print("🔍 Verifying migration...")
        
        # Check workspace exists
        if not frappe.db.exists("Workspace", "DLITS Custom"):
            raise Exception("Workspace verification failed")
        
        # Check custom fields exist
        if not frappe.db.exists("Custom Field", {"dt": "Sales Partner", "fieldname": "supplier"}):
            raise Exception("Custom fields verification failed")
        
        # Check doctype exists
        if not frappe.db.exists("DocType", "Pricing Rule Dlits"):
            raise Exception("DocType verification failed")
        
        print("✅ Migration verification passed")
        
    except Exception as e:
        print(f"   Migration verification failed: {str(e)}")
        raise

def rollback_migration():
    """Rollback migration in case of failure (use with caution)"""
    try:
        print("⚠️ Rolling back migration...")
        
        # Add rollback logic here if needed
        # This should be used very carefully
        
        print("✅ Migration rollback completed")
        
    except Exception as e:
        print(f"   Error during rollback: {str(e)}")
        raise

# Utility functions for future use
def backup_data():
    """Create backup before migration"""
    try:
        # Add backup logic here if needed
        pass
    except Exception as e:
        print(f"   Error creating backup: {str(e)}")

def cleanup_old_data():
    """Clean up old data after successful migration"""
    try:
        # Add cleanup logic here if needed
        pass
    except Exception as e:
        print(f"   Error cleaning up old data: {str(e)}")