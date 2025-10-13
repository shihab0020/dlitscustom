# Copyright (c) 2024, DLITS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, formatdate


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	"""Define report columns"""
	return [
		{
			"fieldname": "name",
			"label": _("Transfer ID"),
			"fieldtype": "Link",
			"options": "Tools Transfer Dlits",
			"width": 120
		},
		{
			"fieldname": "date",
			"label": _("Date"),
			"fieldtype": "Date",
			"width": 100
		},
		{
			"fieldname": "item",
			"label": _("Item Code"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 120
		},
		{
			"fieldname": "item_name",
			"label": _("Item Name"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "qty",
			"label": _("Quantity"),
			"fieldtype": "Float",
			"width": 100,
			"precision": 3
		},
		{
			"fieldname": "uom",
			"label": _("UOM"),
			"fieldtype": "Link",
			"options": "UOM",
			"width": 80
		},
		{
			"fieldname": "source_type",
			"label": _("Source Type"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "source",
			"label": _("Source"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "to_type",
			"label": _("To Type"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "to",
			"label": _("To"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "status",
			"label": _("Status"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "notes",
			"label": _("Notes"),
			"fieldtype": "Data",
			"width": 200
		}
	]


def get_data(filters):
	"""Get report data based on filters"""
	conditions = get_conditions(filters)
	
	query = """
		SELECT 
			tt.name,
			tt.date,
			tt.item,
			tt.item_name,
			tt.qty,
			tt.uom,
			tt.source_type,
			CASE 
				WHEN tt.source_type = 'Warehouse' THEN tt.source_warehouse
				WHEN tt.source_type = 'Employee' THEN CONCAT(tt.source_employee, ' - ', emp1.employee_name)
				ELSE ''
			END as source,
			tt.to_type,
			CASE
				WHEN tt.to_type = 'Warehouse' THEN tt.to_warehouse
				WHEN tt.to_type = 'Employee' THEN CONCAT(tt.to_employee, ' - ', emp2.employee_name)
				ELSE ''
			END as `to`,
			tt.status,
			tt.notes
		FROM `tabTools Transfer Dlits` tt
		LEFT JOIN `tabEmployee` emp1 ON tt.source_employee = emp1.name
		LEFT JOIN `tabEmployee` emp2 ON tt.to_employee = emp2.name
		WHERE tt.docstatus != 2 {conditions}
		ORDER BY tt.date DESC, tt.creation DESC
	""".format(conditions=conditions)
	
	data = frappe.db.sql(query, filters, as_dict=1)
	
	return data


def get_conditions(filters):
	"""Build WHERE conditions based on filters"""
	conditions = []
	
	if filters.get("from_date"):
		conditions.append("tt.date >= %(from_date)s")
	
	if filters.get("to_date"):
		conditions.append("tt.date <= %(to_date)s")
	
	if filters.get("item"):
		conditions.append("tt.item = %(item)s")
	
	if filters.get("status"):
		conditions.append("tt.status = %(status)s")
	
	if filters.get("employee"):
		conditions.append("(tt.source_employee = %(employee)s OR tt.to_employee = %(employee)s)")
	
	if filters.get("warehouse"):
		conditions.append("(tt.source_warehouse = %(warehouse)s OR tt.to_warehouse = %(warehouse)s)")
	
	if filters.get("source_type"):
		conditions.append("tt.source_type = %(source_type)s")
	
	if filters.get("to_type"):
		conditions.append("tt.to_type = %(to_type)s")
	
	return " AND " + " AND ".join(conditions) if conditions else ""


def get_report_summary(data):
	"""Generate report summary"""
	if not data:
		return []
	
	total_transfers = len(data)
	completed_transfers = len([d for d in data if d.get("status") == "Completed"])
	draft_transfers = len([d for d in data if d.get("status") == "Draft"])
	cancelled_transfers = len([d for d in data if d.get("status") == "Cancelled"])
	
	return [
		{
			"value": total_transfers,
			"label": _("Total Transfers"),
			"datatype": "Int"
		},
		{
			"value": completed_transfers,
			"label": _("Completed"),
			"datatype": "Int"
		},
		{
			"value": draft_transfers,
			"label": _("Draft"),
			"datatype": "Int"
		},
		{
			"value": cancelled_transfers,
			"label": _("Cancelled"),
			"datatype": "Int"
		}
	]