frappe.ui.form.on("Sales Order", {
	refresh(frm) {
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(
				__("Dlits Stock Transfer Request"),
				() => {
					frappe.model.open_mapped_doc({
						method: "dlitscustom.dlitscustom.doctype.dlits_stock_transfer_request.dlits_stock_transfer_request.make_stock_transfer_from_so",
						frm: frm,
					});
				},
				__("Create")
			);
		}
	},
});
