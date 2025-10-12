// Copyright (c) 2024, DLITS and contributors
// For license information, please see license.txt

frappe.query_reports["DLITS Supplier Ledger Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_days(frappe.datetime.get_today(), -30),
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname": "supplier",
			"label": __("Supplier"),
			"fieldtype": "Link",
			"options": "Supplier"
		},
		{
			"fieldname": "supplier_group",
			"label": __("Supplier Group"),
			"fieldtype": "Link",
			"options": "Supplier Group"
		},
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname": "show_zero_balance",
			"label": __("Show Zero Balance Suppliers"),
			"fieldtype": "Check",
			"default": 0
		}
	],
	
	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		if (column.fieldname == "balance" && data) {
			if (data.balance > 0) {
				value = "<span style='color:red'>" + value + "</span>";
			} else if (data.balance < 0) {
				value = "<span style='color:green'>" + value + "</span>";
			}
		}
		
		if (column.fieldname == "days_outstanding" && data && data.days_outstanding) {
			if (data.days_outstanding > 90) {
				value = "<span style='color:red; font-weight:bold'>" + value + "</span>";
			} else if (data.days_outstanding > 60) {
				value = "<span style='color:orange; font-weight:bold'>" + value + "</span>";
			} else if (data.days_outstanding > 30) {
				value = "<span style='color:#ffc107; font-weight:bold'>" + value + "</span>";
			}
		}
		
		if (column.fieldname == "document_type" && data) {
			if (data.document_type == "Opening Balance" || data.document_type == "Closing Balance") {
				value = "<span style='font-weight:bold; color:#6c757d'>" + value + "</span>";
			}
		}
		
		return value;
	},
	
	"onload": function(report) {
		// Add custom buttons
		report.page.add_inner_button(__("Export to Excel"), function() {
			frappe.query_report.export_report('DLITS Supplier Ledger Report', 'Excel');
		});
		
		report.page.add_inner_button(__("Export to PDF"), function() {
			frappe.query_report.export_report('DLITS Supplier Ledger Report', 'PDF');
		});
		
		report.page.add_inner_button(__("Print"), function() {
			frappe.query_report.print_report('DLITS Supplier Ledger Report');
		});
	}
};