import calendar
import frappe
from frappe import _
from frappe.utils import cstr, getdate, add_to_date

def execute(filters=None):
    if not filters: filters = {}
    
    common_columns = [
        {"label": _("New Customers"), "fieldname": "new_customers", "fieldtype": "Int", "width": 125},
        {"label": _("Repeat Customers"), "fieldname": "repeat_customers", "fieldtype": "Int", "width": 125},
        {"label": _("Total"), "fieldname": "total", "fieldtype": "Int", "width": 100},
        {"label": _("New Customer Revenue"), "fieldname": "new_customer_revenue", "fieldtype": "Currency", "width": 160},
        {"label": _("Repeat Customer Revenue"), "fieldname": "repeat_customer_revenue", "fieldtype": "Currency", "width": 160},
        {"label": _("Total Revenue"), "fieldname": "total_revenue", "fieldtype": "Currency", "width": 160},
    ]

    if filters.get("view_type") == "Monthly":
        columns, data = get_data_by_time(filters, common_columns)
        chart = get_chart_data(data, filters)
        return columns, data, None, chart, None, None
    else:
        # Fallback to empty if territory is not yet implemented
        return common_columns, [], None, None, None, None

def get_data_by_time(filters, common_columns):
    columns = [
        {"label": _("Year"), "fieldname": "year", "fieldtype": "Data", "width": 80},
        {"label": _("Month"), "fieldname": "month", "fieldtype": "Data", "width": 100},
    ] + common_columns + [
        # Using fieldtype 'Data' for hidden lists to avoid UI overhead
        {"label": "New List", "fieldname": "new_customers_list", "fieldtype": "Data", "hidden": 1},
        {"label": "Repeat List", "fieldname": "repeat_customers_list", "fieldtype": "Data", "hidden": 1}
    ]

    stats, details = get_customer_stats(filters)
    from_date = getdate(filters.get("from_date"))
    to_date = getdate(filters.get("to_date"))

    out = []
    curr_date = from_date.replace(day=1)
    while curr_date <= to_date:
        key = curr_date.strftime("%Y-%m")
        p_stats = stats.get(key, {"new": [0, 0.0], "repeat": [0, 0.0]})
        p_details = details.get(key, {"new": [], "repeat": []})
        
        out.append({
            "year": cstr(curr_date.year),
            "month": calendar.month_name[curr_date.month],
            "new_customers": p_stats["new"][0],
            "repeat_customers": p_stats["repeat"][0],
            "total": p_stats["new"][0] + p_stats["repeat"][0],
            "new_customer_revenue": p_stats["new"][1],
            "repeat_customer_revenue": p_stats["repeat"][1],
            "total_revenue": p_stats["new"][1] + p_stats["repeat"][1],
            "new_customers_list": "||".join(p_details["new"]), 
            "repeat_customers_list": "||".join(p_details["repeat"])
        })
        curr_date = add_to_date(curr_date, months=1)

    return columns, out

def get_customer_stats(filters, tree_view=False):
    # Determine 'New' vs 'Repeat' based on the very first invoice date in history
    
    # Build dynamic conditions for Cost Center
    conditions = ""
    if filters.get("cost_center"):
        conditions += " AND cost_center = %(cost_center)s"

    invoices = frappe.db.sql(f"""
        SELECT territory, posting_date, customer, base_grand_total 
        FROM `tabSales Invoice`
        WHERE docstatus=1 
          AND company=%(company)s 
          {conditions}
          AND posting_date <= %(to_date)s
        ORDER BY posting_date ASC
    """, filters, as_dict=1)

    known_customers = set()
    stats = {}
    details = {}

    for si in invoices:
        is_new = si.customer not in known_customers
        known_customers.add(si.customer)

        if getdate(si.posting_date) < getdate(filters.from_date):
            continue

        key = si.posting_date.strftime("%Y-%m")
        stats.setdefault(key, {"new": [0, 0.0], "repeat": [0, 0.0]})
        details.setdefault(key, {"new": [], "repeat": []})

        type_key = "new" if is_new else "repeat"
        stats[key][type_key][0] += 1
        stats[key][type_key][1] += si.base_grand_total
        
        if si.customer not in details[key][type_key]:
            details[key][type_key].append(si.customer)

    return stats, details

def get_chart_data(data, filters):
    if not data: return None
    return {
        "data": {
            "labels": [f"{d['month'][:3]} {d['year']}" for d in data],
            "datasets": [
                {"name": _("New"), "values": [d["new_customers"] for d in data]},
                {"name": _("Repeat"), "values": [d["repeat_customers"] for d in data]}
            ]
        },
        "type": "bar",
        "colors": ["#4CAF50", "#2196F3"],
    }