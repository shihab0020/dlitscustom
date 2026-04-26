frappe.ui.form.on("Project", {
	refresh(frm) {
		if (frm.doc.docstatus !== 2) {
			frm.add_custom_button(
				__("Dlits Stock Transfer Request"),
				() => {
					frappe.call({
						method: "dlitscustom.dlitscustom.doctype.dlits_stock_transfer_request.dlits_stock_transfer_request.make_stock_transfer_from_project",
						args: { project: frm.doc.name },
						callback(r) {
							if (r.message) {
								frappe.model.sync(r.message);
								frappe.set_route("Form", "Dlits Stock Transfer Request", r.message.name);
							}
						},
					});
				},
				__("Create")
			);
		}
	},
});
