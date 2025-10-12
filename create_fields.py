#!/usr/bin/env python3

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, '/home/shihab/frappe-bench')

# Set environment variables
os.environ['FRAPPE_SITE'] = 'all'

# Import frappe
import frappe

def create_fields():
    """Create commission custom fields"""
    try:
        # Initialize frappe
        frappe.init(site='all')
        frappe.connect()
        
        print("Creating commission custom fields...")
        
        # Import and run the function
        from apps.dlitscustom.dlitscustom.fixtures.custom_fields import create_commission_custom_fields
        create_commission_custom_fields()
        
        # Commit to database
        frappe.db.commit()
        
        print("Commission custom fields created successfully!")
        print("Please refresh your Sales Invoice and Sales Order forms.")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        frappe.destroy()

if __name__ == "__main__":
    create_fields()