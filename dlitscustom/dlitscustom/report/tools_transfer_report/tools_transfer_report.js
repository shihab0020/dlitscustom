// Copyright (c) 2024, DLITS and contributors
// For license information, please see license.txt

frappe.query_reports["Tools Transfer Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 0
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 0
		},
		{
			"fieldname": "item",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item",
			"get_query": function() {
				return {
					"filters": {
						"is_stock_item": 1
					}
				}
			}
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee"
		},
		{
			"fieldname": "warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse"
		},
		{
			"fieldname": "source_type",
			"label": __("Source Type"),
			"fieldtype": "Select",
			"options": "\nWarehouse\nEmployee"
		},
		{
			"fieldname": "to_type",
			"label": __("To Type"),
			"fieldtype": "Select",
			"options": "\nWarehouse\nEmployee"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nDraft\nCompleted\nCancelled",
			"default": "Completed"
		}
	],
	
	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		if (column.fieldname == "status") {
			if (value == "Completed") {
				value = `<span class="indicator green">${value}</span>`;
			} else if (value == "Draft") {
				value = `<span class="indicator orange">${value}</span>`;
			} else if (value == "Cancelled") {
				value = `<span class="indicator red">${value}</span>`;
			}
		}
		
		return value;
	},
	
	"onload": function(report) {
		// Add custom buttons
		report.page.add_inner_button(__("Tools Allocation Summary"), function() {
			frappe.set_route("query-report", "Employee Tools Allocation Summary");
		});
		
		report.page.add_inner_button(__("New Transfer"), function() {
			frappe.new_doc("Tools Transfer Dlits");
		});
	}
};