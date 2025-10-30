// Copyright (c) 2024, DLITS and contributors
// For license information, please see license.txt

frappe.query_reports["DLITS Sales Analytics"] = {
	filters: [
		{
			fieldname: "tree_type",
			label: __("Tree Type"),
			fieldtype: "Select",
			options: [
				"Customer Group",
				"Customer",
				"Supplier Group",
				"Supplier",
				"Item Group",
				"Item",
				"Territory",
				"Order Type",
				"Project",
			],
			default: "Customer",
			reqd: 1,
		},
		{
			fieldname: "doc_type",
			label: __("Based On"),
			fieldtype: "Select",
			options: [
				"All",
				"Quotation",
				"Sales Order",
				"Delivery Note",
				"Sales Invoice",
				"Sales Invoice (due)",
				"Payment Entry",
				"Purchase Order",
				"Purchase Invoice",
				"Purchase Invoice (due)",
			],
			default: "Sales Invoice",
			reqd: 1,
		},
		{
			fieldname: "value_quantity",
			label: __("Value Or Qty"),
			fieldtype: "Select",
			options: [
				"Value",
				"Quantity",
			],
			default: "Value",
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default:
				frappe.defaults.get_user_default("sales_start_date") ||
				erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[1],
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default:
				frappe.defaults.get_user_default("sales_end_date") ||
				erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[2],
			reqd: 1,
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: "Alejtihadat Trading Est.",
			reqd: 1,
		},
		{
			fieldname: "range",
			label: __("Range"),
			fieldtype: "Select",
			options: [
				"Weekly",
				"Monthly",
				"Quarterly",
				"Yearly",
			],
			default: "Monthly",
			reqd: 1,
		},
		{
			fieldname: "curves",
			label: __("Curves"),
			fieldtype: "Select",
			options: [
				"select",
				"all",
				"non-zeros",
				"total",
			],
			default: "total",
			reqd: 1,
		},
		{
			fieldname: "chart_type",
			label: __("Chart Type"),
			fieldtype: "Select",
			options: [
				"line",
				"bar",
				"pie",
				"doughnut",
				"area",
			],
			default: "bar",
			reqd: 1,
		},
		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "Link",
			options: "Cost Center",
			mandatory: 0,
		},
		{
			fieldname: "show_aggregate_value_from_subsidiary_companies",
			label: __("Show Aggregate Value from Subsidiary Companies"),
			fieldtype: "Check",
		},
		{
			fieldname: "additional_filters",
			label: __("Additional Filters"),
			fieldtype: "Small Text",
			default: "cost_center != 'Tax Filing - ATE' OR cost_center != 'XT-EXP - ATE'",
			css_class: "additional-filters-compact",
		},
		// {
		// 	fieldname: "additional_filters_help",
		// 	label: __("Additional Filters Help"),
		// 	fieldtype: "HTML",
		// 	options: `<div>How to use Additional Filters:<br> cost_center != 'Tax Filing - ATE'<br>• customer_group == 'VIP'<br>Supported operators:</strong> ==, !=, <, <=, >, >=, like, not like, in, not in<br>Combine conditions: Use AND/OR to combine multiple conditions</div>`,
		// },
	],
	onload: function(report) {
		// Apply custom CSS to make the additional filters field more compact
		setTimeout(() => {
			const additionalFiltersField = $(`[data-fieldname="additional_filters"] textarea`);
			if (additionalFiltersField.length) {
				additionalFiltersField.css({
					'height': '60px',
					'min-height': '60px',
					'max-height': '80px',
					'resize': 'vertical',
					'width': '100%'
				});
			}
		}, 100);
	},
	get_datatable_options(options) {
		return Object.assign(options, {
			checkboxColumn: true,
			events: {
				onCheckRow: function (data) {
					if (!data) return;
					const data_doctype = $(data[2].html)[0].attributes.getNamedItem("data-doctype").value;
					const tree_type = frappe.query_report.filters[0].value;
					if (data_doctype != tree_type) return;

					const row_name = data[2].content;
					const raw_data = frappe.query_report.chart.data;
					const new_datasets = raw_data.datasets;
					const element_found = new_datasets.some((element, index, array) => {
						if (element.name == row_name) {
							array.splice(index, 1);
							return true;
						}
						return false;
					});
					const slice_at = { Customer: 4, Item: 5 }[tree_type] || 3;

					if (!element_found) {
						new_datasets.push({
							name: row_name,
							values: data.slice(slice_at, data.length - 1).map((column) => column.content),
						});
					}

					const new_data = {
						labels: raw_data.labels,
						datasets: new_datasets,
					};
					const new_options = Object.assign({}, frappe.query_report.chart_options, {
						data: new_data,
					});
					frappe.query_report.render_chart(new_options);

					frappe.query_report.raw_chart_data = new_data;
				},
			},
		});
	},
};