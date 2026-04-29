const DSTR_METHODS = "dlitscustom.dlitscustom.doctype.dlits_stock_transfer_request.dlits_stock_transfer_request";

frappe.ui.form.on("Dlits Stock Transfer Request", {

	refresh(frm) {
		frm.trigger("render_status_badge");
		frm.trigger("setup_get_items_button");
	},

	render_status_badge(frm) {
		const colours = {
			"Draft": "grey",
			"Pending Approval": "orange",
			"Approved": "green",
			"Rejected": "red",
			"Delivered": "blue",
			"Received": "purple",
			"Completed": "green",
			"Cancelled": "red",
		};
		frm.page.set_indicator(frm.doc.status, colours[frm.doc.status] || "grey");
	},

	reference_type(frm) { frm.trigger("setup_get_items_button"); },
	reference_name(frm) { frm.trigger("setup_get_items_button"); },

	setup_get_items_button(frm) {
		if (frm.doc.reference_type !== "Sales Order"
				|| !frm.doc.reference_name
				|| frm.doc.docstatus !== 0) return;

		frm.add_custom_button(__("Get Items from Sales Order"), () => {
			frappe.call({
				method: `${DSTR_METHODS}.get_items_from_sales_order`,
				args: { sales_order: frm.doc.reference_name },
				freeze: true,
				freeze_message: __("Fetching items…"),
				callback(r) {
					if (!r.message || !r.message.length) {
						frappe.msgprint(__("No items found in the selected Sales Order."));
						return;
					}
					const hasItems = frm.doc.items && frm.doc.items.length;
					const doFetch = () => {
						frm.clear_table("items");
						r.message.forEach(item => {
							const row = frm.add_child("items");
							frappe.model.set_value(row.doctype, row.name, "item_code", item.item_code);
							frappe.model.set_value(row.doctype, row.name, "item_name", item.item_name);
							frappe.model.set_value(row.doctype, row.name, "qty", item.qty);
							frappe.model.set_value(row.doctype, row.name, "uom", item.uom);
							if (item.remarks) {
								frappe.model.set_value(row.doctype, row.name, "remarks", item.remarks);
							}
						});
						frm.refresh_field("items");
						frappe.show_alert({
							message: __("{0} item(s) fetched from Sales Order").replace("{0}", r.message.length),
							indicator: "green",
						});
					};

					if (hasItems) {
						frappe.confirm(
							__("This will replace the existing {0} item(s). Continue?").replace("{0}", frm.doc.items.length),
							doFetch
						);
					} else {
						doFetch();
					}
				},
			});
		}, __("Tools"));
	},
});
