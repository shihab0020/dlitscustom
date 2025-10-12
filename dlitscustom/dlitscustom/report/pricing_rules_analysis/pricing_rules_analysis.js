// Copyright (c) 2024, DLITS and contributors
// For license information, please see license.txt

frappe.query_reports["Pricing Rules Analysis"] = {
	"filters": [
		{
			"fieldname": "enabled",
			"label": __("Show Only Enabled"),
			"fieldtype": "Check",
			"default": 0
		},
		{
			"fieldname": "price_list",
			"label": __("Price List"),
			"fieldtype": "Link",
			"options": "Price List"
		},
		{
			"fieldname": "base_price_type",
			"label": __("Base Price Type"),
			"fieldtype": "Select",
			"options": "\nPrice List Rate\nValuation Rate\nSelling Rate\nItem Rate"
		},
		{
			"fieldname": "apply_on",
			"label": __("Apply On"),
			"fieldtype": "Select",
			"options": "\nItem Code\nItem Group\nBrand"
		},
		{
			"fieldname": "apply_to",
			"label": __("Apply To"),
			"fieldtype": "Select",
			"options": "\nCustomer\nCustomer Group"
		},
		{
			"fieldname": "from_date",
			"label": __("Created From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -3)
		},
		{
			"fieldname": "to_date",
			"label": __("Created To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "usage_from_date",
			"label": __("Usage From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			"fieldname": "usage_to_date",
			"label": __("Usage To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		}
	],
	
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		if (column.fieldname == "enabled" && data && data.enabled == 1) {
			value = `<span class="indicator green">Enabled</span>`;
		} else if (column.fieldname == "enabled" && data && data.enabled == 0) {
			value = `<span class="indicator red">Disabled</span>`;
		}
		
		if (column.fieldname == "base_price_type" && data) {
			let color = "blue";
			if (data.base_price_type == "Item Rate") color = "purple";
			else if (data.base_price_type == "Selling Rate") color = "green";
			else if (data.base_price_type == "Valuation Rate") color = "orange";
			
			value = `<span class="indicator ${color}">${data.base_price_type}</span>`;
		}
		
		if (column.fieldname == "priority" && data && data.priority == 0) {
			value = `<span class="text-muted">Default</span>`;
		}
		
		return value;
	},
	
	"onload": function(report) {
		// Add custom buttons
		report.page.add_inner_button(__("Create New Pricing Rule"), function() {
			frappe.new_doc("Pricing Rule Dlits");
		});
		
		report.page.add_inner_button(__("Pricing Rule Settings"), function() {
			frappe.set_route("List", "Pricing Rule Dlits");
		});
		
		report.page.add_inner_button(__("Test Pricing Rule"), function() {
			let d = new frappe.ui.Dialog({
				title: __("Test Pricing Rule"),
				fields: [
					{
						fieldname: "item_code",
						label: __("Item Code"),
						fieldtype: "Link",
						options: "Item",
						reqd: 1
					},
					{
						fieldname: "customer",
						label: __("Customer"),
						fieldtype: "Link",
						options: "Customer"
					},
					{
						fieldname: "price_list",
						label: __("Price List"),
						fieldtype: "Link",
						options: "Price List",
						default: "Standard Selling"
					}
				],
				primary_action_label: __("Test"),
				primary_action: function(values) {
					frappe.call({
						method: "dlitscustom.utils.get_pricing_rule_dlits.get_pricing_rule_dlits",
						args: {
							item_code: values.item_code,
							customer: values.customer,
							price_list: values.price_list
						},
						callback: function(r) {
							if (r.message) {
								frappe.msgprint({
									title: __("Pricing Rule Result"),
									message: __("Calculated Price: {0}", [r.message]),
									indicator: "green"
								});
							} else {
								frappe.msgprint({
									title: __("No Pricing Rule"),
									message: __("No pricing rule found for the given criteria"),
									indicator: "orange"
								});
							}
						}
					});
					d.hide();
				}
			});
			d.show();
		});
	}
};