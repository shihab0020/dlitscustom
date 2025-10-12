# Copyright (c) 2024, DLITS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, today

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "label": _("Pricing Rule"),
            "fieldname": "name",
            "fieldtype": "Link",
            "options": "Pricing Rule Dlits",
            "width": 150
        },
        {
            "label": _("Enabled"),
            "fieldname": "enabled",
            "fieldtype": "Check",
            "width": 80
        },
        {
            "label": _("Priority"),
            "fieldname": "priority",
            "fieldtype": "Int",
            "width": 80
        },
        {
            "label": _("Price List"),
            "fieldname": "price_list",
            "fieldtype": "Link",
            "options": "Price List",
            "width": 120
        },
        {
            "label": _("Base Price Type"),
            "fieldname": "base_price_type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Discount Type"),
            "fieldname": "discount_type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Discount Value"),
            "fieldname": "discount_value",
            "fieldtype": "Float",
            "width": 100
        },
        {
            "label": _("Apply On"),
            "fieldname": "apply_on",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Apply To"),
            "fieldname": "apply_to",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Items Count"),
            "fieldname": "items_count",
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("Customers Count"),
            "fieldname": "customers_count",
            "fieldtype": "Int",
            "width": 120
        },
        {
            "label": _("Usage Count"),
            "fieldname": "usage_count",
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("Last Used"),
            "fieldname": "last_used",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("Created On"),
            "fieldname": "creation",
            "fieldtype": "Datetime",
            "width": 120
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    # Get pricing rules with counts
    data = frappe.db.sql(f"""
        SELECT 
            pr.name,
            pr.enabled,
            pr.priority,
            pr.price_list,
            pr.base_price_type,
            pr.discount_type,
            pr.discount_value,
            pr.apply_on,
            pr.apply_to,
            pr.creation,
            
            -- Count items
            (SELECT COUNT(*) FROM `tabPricing Rule Item Code Dlits` 
             WHERE parent = pr.name) as items_count,
            
            -- Count customers
            (SELECT COUNT(*) FROM `tabPricing Rule Customer Dlits` 
             WHERE parent = pr.name) as customers_count,
            
            -- Count item groups
            (SELECT COUNT(*) FROM `tabPricing Rule Item Group Dlits` 
             WHERE parent = pr.name) as item_groups_count,
            
            -- Count brands
            (SELECT COUNT(*) FROM `tabPricing Rule Brand Dlits` 
             WHERE parent = pr.name) as brands_count,
            
            -- Count customer groups
            (SELECT COUNT(*) FROM `tabPricing Rule Customer Group Dlits` 
             WHERE parent = pr.name) as customer_groups_count
             
        FROM `tabPricing Rule Dlits` pr
        WHERE 1=1 {conditions}
        ORDER BY pr.priority ASC, pr.creation DESC
    """, as_dict=True)
    
    # Get usage statistics for each pricing rule
    for row in data:
        usage_stats = get_pricing_rule_usage_stats(row.name, filters)
        row.update(usage_stats)
        
        # Calculate total apply targets
        if row.apply_on == "Item Code":
            row.apply_targets_count = row.items_count
        elif row.apply_on == "Item Group":
            row.apply_targets_count = row.item_groups_count
        elif row.apply_on == "Brand":
            row.apply_targets_count = row.brands_count
        
        if row.apply_to == "Customer":
            row.apply_to_count = row.customers_count
        elif row.apply_to == "Customer Group":
            row.apply_to_count = row.customer_groups_count
    
    return data

def get_conditions(filters):
    conditions = ""
    
    if filters.get("enabled"):
        conditions += " AND pr.enabled = 1"
    
    if filters.get("price_list"):
        conditions += f" AND pr.price_list = '{filters.get('price_list')}'"
    
    if filters.get("base_price_type"):
        conditions += f" AND pr.base_price_type = '{filters.get('base_price_type')}'"
    
    if filters.get("apply_on"):
        conditions += f" AND pr.apply_on = '{filters.get('apply_on')}'"
    
    if filters.get("apply_to"):
        conditions += f" AND pr.apply_to = '{filters.get('apply_to')}'"
    
    if filters.get("from_date"):
        conditions += f" AND DATE(pr.creation) >= '{filters.get('from_date')}'"
    
    if filters.get("to_date"):
        conditions += f" AND DATE(pr.creation) <= '{filters.get('to_date')}'"
    
    return conditions

def get_pricing_rule_usage_stats(pricing_rule_name, filters):
    """Get usage statistics for a pricing rule"""
    
    # Get date range for usage stats
    from_date = filters.get("usage_from_date") or frappe.utils.add_months(today(), -3)
    to_date = filters.get("usage_to_date") or today()
    
    # This is a simplified approach - in a real implementation, you would need to
    # track pricing rule usage in sales transactions
    
    # For now, return placeholder data
    return {
        "usage_count": 0,
        "last_used": None
    }

def get_chart_data(data, filters):
    """Generate chart data for the report"""
    
    # Base Price Type Distribution
    base_price_types = {}
    enabled_count = 0
    disabled_count = 0
    
    for row in data:
        # Count by base price type
        base_price_type = row.get("base_price_type", "Unknown")
        base_price_types[base_price_type] = base_price_types.get(base_price_type, 0) + 1
        
        # Count enabled/disabled
        if row.get("enabled"):
            enabled_count += 1
        else:
            disabled_count += 1
    
    return {
        "data": {
            "labels": list(base_price_types.keys()),
            "datasets": [
                {
                    "name": "Pricing Rules by Base Price Type",
                    "values": list(base_price_types.values())
                }
            ]
        },
        "type": "donut",
        "height": 300
    }