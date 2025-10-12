// Copyright (c) 2024, DLITS and contributors
// For license information, please see license.txt

frappe.query_reports["DLITS Sales Partner Commission Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -3),
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
			"fieldname": "sales_partner",
			"label": __("DLITS Sales Partner"),
			"fieldtype": "Link",
			"options": "DLITS Sales Partner"
		},
		{
			"fieldname": "commission_rate_min",
			"label": __("Min Commission Rate (%)"),
			"fieldtype": "Float"
		},
		{
			"fieldname": "commission_rate_max",
			"label": __("Max Commission Rate (%)"),
			"fieldtype": "Float"
		},
		{
			"fieldname": "include_disabled",
			"label": __("Include Disabled"),
			"fieldtype": "Check",
			"default": 0
		},
		{
			"fieldname": "show_all",
			"label": __("Show All (Including Zero Commission)"),
			"fieldtype": "Check",
			"default": 0
		}
	],
	
	"formatter": function(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		
		if (column.fieldname == "payment_status" && data) {
			let color = "blue";
			if (data.payment_status == "Fully Paid") color = "green";
			else if (data.payment_status == "Unpaid") color = "red";
			else if (data.payment_status == "Partially Paid") color = "orange";
			else if (data.payment_status == "No Commission") color = "gray";
			
			value = `<span class="indicator ${color}">${data.payment_status}</span>`;
		}
		
		if (column.fieldname == "outstanding_commission" && data && data.outstanding_commission > 0) {
			value = `<span class="text-danger"><strong>${value}</strong></span>`;
		}
		
		if (column.fieldname == "commission_rate" && data && data.commission_rate) {
			value = `${data.commission_rate}%`;
		}
		
		return value;
	},
	
	"onload": function(report) {
		// Add custom buttons
		report.page.add_inner_button(__("Create Commission Payment"), function() {
			let selected_rows = report.datatable.rowmanager.getCheckedRows();
			if (selected_rows.length === 0) {
				frappe.msgprint(__("Please select at least one sales partner"));
				return;
			}
			
			let sales_partners = selected_rows.map(row => {
				let data = report.data[row];
				return {
					sales_partner: data.sales_partner,
					partner_name: data.partner_name,
					outstanding_commission: data.outstanding_commission,
					linked_supplier: data.linked_supplier
				};
			});
			
			show_commission_payment_dialog(sales_partners);
		});
		
		report.page.add_inner_button(__("Outstanding Commissions"), function() {
			frappe.call({
				method: "dlitscustom.utils.commission_management_dlits.get_outstanding_commissions",
				args: {
					from_date: report.get_filter_value("from_date"),
					to_date: report.get_filter_value("to_date")
				},
				callback: function(r) {
					if (r.message && r.message.length > 0) {
						show_outstanding_commissions_dialog(r.message);
					} else {
						frappe.msgprint(__("No outstanding commissions found"));
					}
				}
			});
		});
		
		report.page.add_inner_button(__("Commission Summary"), function() {
			let sales_partner = report.get_filter_value("sales_partner");
			if (!sales_partner) {
				frappe.msgprint(__("Please select a DLITS Sales Partner first"));
				return;
			}
			
			frappe.call({
				method: "dlitscustom.utils.commission_management_dlits.get_sales_partner_commission_summary",
				args: {
					sales_partner: sales_partner,
					from_date: report.get_filter_value("from_date"),
					to_date: report.get_filter_value("to_date")
				},
				callback: function(r) {
					if (r.message) {
						show_commission_summary_dialog(r.message);
					}
				}
			});
		});
		
		report.page.add_inner_button(__("Export Outstanding"), function() {
			let outstanding_data = report.data.filter(row => row.outstanding_commission > 0);
			if (outstanding_data.length === 0) {
				frappe.msgprint(__("No outstanding commissions to export"));
				return;
			}
			
			// Create CSV content
			let csv_content = "Sales Partner,Partner Name,Outstanding Commission,Linked Supplier\n";
			outstanding_data.forEach(row => {
				csv_content += `"${row.sales_partner}","${row.partner_name}","${row.outstanding_commission}","${row.linked_supplier || ''}"\n`;
			});
			
			// Download CSV
			let blob = new Blob([csv_content], { type: 'text/csv' });
			let url = window.URL.createObjectURL(blob);
			let a = document.createElement('a');
			a.href = url;
			a.download = `outstanding_commissions_${frappe.datetime.get_today()}.csv`;
			a.click();
			window.URL.revokeObjectURL(url);
		});
	}
};

function show_commission_payment_dialog(sales_partners) {
	let total_outstanding = sales_partners.reduce((sum, sp) => sum + (sp.outstanding_commission || 0), 0);
	
	let d = new frappe.ui.Dialog({
		title: __("Create Commission Payments"),
		fields: [
			{
				fieldname: "payment_date",
				label: __("Payment Date"),
				fieldtype: "Date",
				default: frappe.datetime.get_today(),
				reqd: 1
			},
			{
				fieldname: "mode_of_payment",
				label: __("Mode of Payment"),
				fieldtype: "Link",
				options: "Mode of Payment",
				reqd: 1
			},
			{
				fieldname: "total_amount",
				label: __("Total Outstanding Amount"),
				fieldtype: "Currency",
				read_only: 1,
				default: total_outstanding
			},
			{
				fieldname: "sales_partners_html",
				fieldtype: "HTML"
			}
		],
		primary_action_label: __("Create Payments"),
		primary_action: function(values) {
			let payments_data = sales_partners.map(sp => ({
				sales_partner: sp.sales_partner,
				amount: sp.outstanding_commission,
				reference_date: values.payment_date
			}));
			
			frappe.call({
				method: "dlitscustom.utils.commission_management_dlits.create_bulk_commission_payments",
				args: {
					sales_partners_data: payments_data
				},
				callback: function(r) {
					if (r.message) {
						let result = r.message;
						let message = `Created ${result.created_payments.length} payment(s)`;
						if (result.errors.length > 0) {
							message += `<br>Errors: ${result.errors.join('<br>')}`;
						}
						frappe.msgprint({
							title: __("Payment Creation Result"),
							message: message,
							indicator: result.errors.length > 0 ? "orange" : "green"
						});
						cur_page.page.page.refresh();
					}
				}
			});
			d.hide();
		}
	});
	
	// Show sales partners table
	let html = `<table class="table table-bordered">
		<thead>
			<tr>
				<th>Sales Partner</th>
				<th>Partner Name</th>
				<th>Outstanding Commission</th>
				<th>Linked Supplier</th>
			</tr>
		</thead>
		<tbody>`;
	
	sales_partners.forEach(sp => {
		html += `<tr>
			<td>${sp.sales_partner}</td>
			<td>${sp.partner_name}</td>
			<td>${format_currency(sp.outstanding_commission)}</td>
			<td>${sp.linked_supplier || 'Not Linked'}</td>
		</tr>`;
	});
	
	html += `</tbody></table>`;
	d.fields_dict.sales_partners_html.$wrapper.html(html);
	d.show();
}

function show_outstanding_commissions_dialog(outstanding_data) {
	let d = new frappe.ui.Dialog({
		title: __("Outstanding Commissions Summary"),
		size: "large",
		fields: [
			{
				fieldname: "outstanding_html",
				fieldtype: "HTML"
			}
		]
	});
	
	let total_outstanding = outstanding_data.reduce((sum, item) => sum + item.outstanding_commission, 0);
	
	let html = `<div class="row">
		<div class="col-md-12">
			<h4>Total Outstanding: ${format_currency(total_outstanding)}</h4>
			<table class="table table-bordered">
				<thead>
					<tr>
						<th>Sales Partner</th>
						<th>Partner Name</th>
						<th>Commission Rate</th>
						<th>Total Commission</th>
						<th>Paid Commission</th>
						<th>Outstanding Commission</th>
					</tr>
				</thead>
				<tbody>`;
	
	outstanding_data.forEach(item => {
		html += `<tr>
			<td><a href="/app/dlits-sales-partner/${item.sales_partner}">${item.sales_partner}</a></td>
			<td>${item.partner_name}</td>
			<td>${item.commission_rate}%</td>
			<td>${format_currency(item.total_commission)}</td>
			<td>${format_currency(item.paid_commission)}</td>
			<td><strong>${format_currency(item.outstanding_commission)}</strong></td>
		</tr>`;
	});
	
	html += `</tbody></table></div></div>`;
	d.fields_dict.outstanding_html.$wrapper.html(html);
	d.show();
}

function show_commission_summary_dialog(summary) {
	let d = new frappe.ui.Dialog({
		title: __("Commission Summary for {0}", [summary.sales_partner]),
		size: "large",
		fields: [
			{
				fieldname: "summary_html",
				fieldtype: "HTML"
			}
		]
	});
	
	let html = `<div class="row">
		<div class="col-md-6">
			<h5>Commission Overview</h5>
			<table class="table">
				<tr><td>Total Commission:</td><td><strong>${format_currency(summary.total_commission)}</strong></td></tr>
				<tr><td>Paid Commission:</td><td>${format_currency(summary.paid_commission)}</td></tr>
				<tr><td>Outstanding Commission:</td><td><strong class="text-danger">${format_currency(summary.outstanding_commission)}</strong></td></tr>
			</table>
		</div>
		<div class="col-md-6">
			<h5>Sales Overview</h5>
			<table class="table">
				<tr><td>Total Orders:</td><td>${summary.total_orders}</td></tr>
				<tr><td>Total Sales:</td><td>${format_currency(summary.total_sales)}</td></tr>
				<tr><td>Commission Rate:</td><td>${summary.commission_rate}%</td></tr>
				<tr><td>Linked Supplier:</td><td>${summary.linked_supplier || 'Not Linked'}</td></tr>
			</table>
		</div>
	</div>`;
	
	d.fields_dict.summary_html.$wrapper.html(html);
	d.show();
}