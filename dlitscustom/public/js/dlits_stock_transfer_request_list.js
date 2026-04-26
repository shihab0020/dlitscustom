frappe.listview_settings["Dlits Stock Transfer Request"] = {
	add_fields: ["status", "request_type", "technician_name", "assigned_supervisor", "assigned_showroom_user"],

	get_indicator(doc) {
		const map = {
			"Draft":            ["grey",    "status,=,Draft"],
			"Pending Approval": ["orange",  "status,=,Pending Approval"],
			"Approved":         ["green",   "status,=,Approved"],
			"Rejected":         ["red",     "status,=,Rejected"],
			"Delivered":        ["blue",    "status,=,Delivered"],
			"Received":         ["purple",  "status,=,Received"],
			"Completed":        ["green",   "status,=,Completed"],
			"Cancelled":        ["red",     "status,=,Cancelled"],
		};
		const entry = map[doc.status] || ["grey", `status,=,${doc.status}`];
		return [__(doc.status), entry[0], entry[1]];
	},

	formatters: {
		request_type(val) {
			if (val === "Return") {
				return `<span style="background:#dc3545;color:#fff;padding:1px 7px;border-radius:8px;font-size:11px">↩ Return</span>`;
			}
			return `<span style="background:#0d6efd;color:#fff;padding:1px 7px;border-radius:8px;font-size:11px">→ Transfer</span>`;
		},
	},

	onload(listview) {
		// Quick-filter buttons in the toolbar
		listview.page.add_inner_button(__("My Requests"), () => {
			listview.filter_area.add([["Dlits Stock Transfer Request", "requested_by", "=", frappe.session.user]]);
		});
		listview.page.add_inner_button(__("Pending Approval"), () => {
			listview.filter_area.add([["Dlits Stock Transfer Request", "status", "=", "Pending Approval"]]);
		});
		listview.page.add_inner_button(__("My Deliveries"), () => {
			listview.filter_area.add([["Dlits Stock Transfer Request", "assigned_showroom_user", "=", frappe.session.user]]);
		});
		listview.page.add_inner_button(__("In Progress"), () => {
			listview.filter_area.add([["Dlits Stock Transfer Request", "status", "not in", "Draft,Completed,Cancelled,Rejected"]]);
		});
	},
};
