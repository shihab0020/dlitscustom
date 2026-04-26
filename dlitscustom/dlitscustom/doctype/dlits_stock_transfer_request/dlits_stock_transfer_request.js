const DSTR_METHODS = "dlitscustom.dlitscustom.doctype.dlits_stock_transfer_request.dlits_stock_transfer_request";

frappe.ui.form.on("Dlits Stock Transfer Request", {

	setup(frm) {
		frm.set_query("assigned_supervisor", () => ({
			query: `${DSTR_METHODS}.get_role_user_query`,
			filters: { dlits_role: "Supervisor" },
		}));
		frm.set_query("assigned_showroom_user", () => ({
			query: `${DSTR_METHODS}.get_role_user_query`,
			filters: { dlits_role: "Showroom" },
		}));
	},

	refresh(frm) {
		frm.trigger("render_status_badge");
		frm.trigger("toggle_item_editability");
		frm.trigger("setup_action_buttons");
		frm.trigger("setup_get_items_button");
	},

	// Prevent accidental premature submit via ERPNext's standard Submit button
	before_submit(frm) {
		if (frm.doc.status !== "Received") {
			frappe.msgprint({
				title: __("Cannot Submit Yet"),
				message: __("The request must complete all workflow steps and reach <b>Received</b> status before the supervisor can submit.<br><br>Current status: <b>{0}</b>").replace("{0}", frm.doc.status),
				indicator: "red",
			});
			frappe.validated = false;
		}
	},

	// ── Status badge + headline hint ──────────────────────────────────────────
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

		const hints = {
			"Draft": "Add items, then click <b>Request Approval</b> when ready.",
			"Pending Approval": "Waiting for supervisor approval.",
			"Approved": "Showroom: update items/quantities if needed, Save, then click <b>Mark as Delivered</b>.",
			"Rejected": "Request rejected — check supervisor notes. You may edit and re-request.",
			"Delivered": "Technician: confirm you have received the items by clicking <b>Confirm Receipt</b>.",
			"Received": "Supervisor: review the final items and click the <b>Submit</b> button to create the Stock Entry.",
			"Completed": `Completed. Stock Entry <b>${frm.doc.stock_entry || ""}</b> created.`,
			"Cancelled": "This request has been cancelled.",
		};
		const hint = hints[frm.doc.status];
		if (hint) frm.dashboard.set_headline_alert(hint);
	},

	// ── Item field editability per stage ──────────────────────────────────────
	toggle_item_editability(frm) {
		if (frm.doc.docstatus === 1) return; // submitted — all read only

		const status = frm.doc.status;
		const user = frappe.session.user;
		const isSysManager = frappe.user.has_role("System Manager");
		const isShowroom = user === frm.doc.assigned_showroom_user || isSysManager;
		const isTechnician = user === frm.doc.requested_by || isSysManager;

		// Core fields (item, qty) — editable by technician in Draft, and by showroom in Approved
		const coreEditable = (status === "Draft" && isTechnician)
			|| (status === "Approved" && isShowroom)
			|| (status === "Rejected" && isTechnician);
		frm.fields_dict.items.grid.toggle_enable("item_code", coreEditable);
		frm.fields_dict.items.grid.toggle_enable("qty", coreEditable);

		// delivered_qty — editable by showroom when Approved
		frm.fields_dict.items.grid.toggle_enable("delivered_qty",
			status === "Approved" && isShowroom);

		// received_qty — editable by technician when Delivered
		frm.fields_dict.items.grid.toggle_enable("received_qty",
			status === "Delivered" && isTechnician);
	},

	// ── Action buttons per stage (all in Draft) ───────────────────────────────
	setup_action_buttons(frm) {
		if (frm.doc.docstatus !== 0) return; // submitted/cancelled — no custom actions

		const user = frappe.session.user;
		const status = frm.doc.status;
		const isSysManager = frappe.user.has_role("System Manager");

		// ── DRAFT: Technician requests approval ───────────────────────────────
		if (status === "Draft") {
			const isTechnician = user === frm.doc.requested_by || isSysManager;
			if (isTechnician) {
				const btn = frm.add_custom_button(__("Request Approval"), () => {
					if (!frm.doc.items || !frm.doc.items.length) {
						frappe.msgprint(__("Please add items before requesting approval."));
						return;
					}
					if (frm.is_dirty()) {
						frappe.msgprint(__("Please save the document before requesting approval."));
						return;
					}
					frappe.confirm(
						__("Send this request to the supervisor for approval?"),
						() => frappe.call({
							method: `${DSTR_METHODS}.request_for_approval`,
							args: { name: frm.doc.name },
							callback() {
								frm.reload_doc();
								frappe.show_alert({ message: __("Request sent for approval"), indicator: "orange" });
							},
						})
					);
				});
				btn.removeClass("btn-default").addClass("btn-primary");
			}
		}

		// ── REJECTED: Allow technician to re-request after editing ────────────
		if (status === "Rejected") {
			const isTechnician = user === frm.doc.requested_by || isSysManager;
			if (isTechnician) {
				frm.add_custom_button(__("Re-Request Approval"), () => {
					if (frm.is_dirty()) {
						frappe.msgprint(__("Please save your changes before re-requesting."));
						return;
					}
					frappe.confirm(
						__("Re-submit this request for supervisor approval?"),
						() => frappe.call({
							method: `${DSTR_METHODS}.request_for_approval`,
							args: { name: frm.doc.name },
							callback() {
								frm.reload_doc();
								frappe.show_alert({ message: __("Request re-sent for approval"), indicator: "orange" });
							},
						})
					);
				}).removeClass("btn-default").addClass("btn-warning");
			}
		}

		// ── PENDING APPROVAL: Supervisor approves or rejects ──────────────────
		if (status === "Pending Approval") {
			frappe.call({
				method: `${DSTR_METHODS}.get_supervisor_users`,
				callback(r) {
					const supers = (r.message || []).map(u => u.user);
					if (supers.includes(user) || isSysManager) {
						frm.add_custom_button(__("Approve"), () =>
							frm.trigger("show_approve_dialog"), __("Action"));
						frm.add_custom_button(__("Reject"), () =>
							frm.trigger("show_reject_dialog"), __("Action"));
					}
				},
			});
		}

		// ── APPROVED: Showroom marks delivery ─────────────────────────────────
		if (status === "Approved") {
			if (user === frm.doc.assigned_showroom_user || isSysManager) {
				frm.add_custom_button(__("Mark as Delivered"), () => {
					if (frm.is_dirty()) {
						frappe.msgprint(__("Please save item changes before marking as delivered."));
						return;
					}
					frm.trigger("show_delivery_dialog");
				}, __("Action"));
			}
		}

		// ── DELIVERED: Technician confirms receipt ────────────────────────────
		if (status === "Delivered") {
			if (user === frm.doc.requested_by || isSysManager) {
				frm.add_custom_button(__("Confirm Receipt"), () => {
					if (frm.is_dirty()) {
						frappe.msgprint(__("Please save received quantities before confirming."));
						return;
					}
					frappe.confirm(
						__("Confirm that you have received all items?"),
						() => frappe.call({
							method: `${DSTR_METHODS}.mark_received`,
							args: { name: frm.doc.name },
							callback() {
								frm.reload_doc();
								frappe.show_alert({ message: __("Receipt confirmed"), indicator: "green" });
							},
						})
					);
				}, __("Action"));
			}
		}

		// ── RECEIVED: Supervisor submits (standard Submit button does this) ───
		// The ERPNext Submit button handles this stage — before_submit validates it
	},

	// ── Auto-fill destination warehouse ──────────────────────────────────────
	requested_by(frm) {
		if (!frm.doc.requested_by || frm.doc.destination_warehouse) return;
		frappe.call({
			method: `${DSTR_METHODS}.get_user_warehouse_assignment`,
			args: { user: frm.doc.requested_by },
			callback(r) {
				if (r.message && r.message.default_target_warehouse) {
					frm.set_value("destination_warehouse", r.message.default_target_warehouse);
				}
			},
		});
	},

	// Re-show the Get Items button whenever reference fields change
	reference_type(frm) { frm.trigger("setup_get_items_button"); },
	reference_name(frm) { frm.trigger("setup_get_items_button"); },

	// ── Get Items from Sales Order ────────────────────────────────────────────
	setup_get_items_button(frm) {
		// Only show when linked to a Sales Order, document is still editable
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
					// Ask before replacing existing rows
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

	// ── Dialogs ───────────────────────────────────────────────────────────────
	show_approve_dialog(frm) {
		frappe.call({
			method: `${DSTR_METHODS}.get_showroom_users`,
			callback(r) {
				const showroomUsers = r.message || [];
				const first = showroomUsers[0];

				const d = new frappe.ui.Dialog({
					title: __("Approve Stock Transfer Request"),
					fields: [
						{
							label: __("Assign to Showroom User"),
							fieldname: "assigned_showroom_user",
							fieldtype: "Select",
							options: showroomUsers.map(u => `${u.user}:${u.full_name || u.user}`).join("\n"),
							reqd: 1,
							default: first ? first.user : "",
						},
						{
							label: __("Dispatch From Warehouse"),
							fieldname: "source_warehouse",
							fieldtype: "Link",
							options: "Warehouse",
							reqd: 1,
							default: frm.doc.source_warehouse || (first ? first.default_source_warehouse : ""),
						},
						{ fieldtype: "Column Break" },
						{
							label: __("Supervisor Notes"),
							fieldname: "supervisor_notes",
							fieldtype: "Small Text",
							default: frm.doc.supervisor_notes,
						},
					],
					primary_action_label: __("Approve"),
					primary_action(values) {
						frappe.call({
							method: `${DSTR_METHODS}.approve_request`,
							args: {
								name: frm.doc.name,
								supervisor_notes: values.supervisor_notes,
								source_warehouse: values.source_warehouse,
								assigned_showroom_user: values.assigned_showroom_user,
							},
							callback() {
								d.hide();
								frm.reload_doc();
								frappe.show_alert({ message: __("Request Approved"), indicator: "green" });
							},
						});
					},
				});
				d.show();
			},
		});
	},

	show_reject_dialog(frm) {
		const d = new frappe.ui.Dialog({
			title: __("Reject Stock Transfer Request"),
			fields: [
				{
					label: __("Reason for Rejection"),
					fieldname: "supervisor_notes",
					fieldtype: "Small Text",
					reqd: 1,
				},
			],
			primary_action_label: __("Reject"),
			primary_action(values) {
				frappe.call({
					method: `${DSTR_METHODS}.reject_request`,
					args: { name: frm.doc.name, supervisor_notes: values.supervisor_notes },
					callback() {
						d.hide();
						frm.reload_doc();
						frappe.show_alert({ message: __("Request Rejected"), indicator: "red" });
					},
				});
			},
		});
		d.show();
	},

	show_delivery_dialog(frm) {
		const d = new frappe.ui.Dialog({
			title: __("Confirm Delivery"),
			fields: [
				{
					fieldtype: "HTML",
					options: `<p class="text-muted small">${__("Delivered quantities in the items table will be recorded. Items not updated will default to the requested quantity.")}</p>`,
				},
				{
					label: __("Delivery Notes"),
					fieldname: "showroom_notes",
					fieldtype: "Small Text",
				},
			],
			primary_action_label: __("Confirm Delivered"),
			primary_action(values) {
				frappe.call({
					method: `${DSTR_METHODS}.mark_delivered`,
					args: { name: frm.doc.name, showroom_notes: values.showroom_notes },
					callback() {
						d.hide();
						frm.reload_doc();
						frappe.show_alert({ message: __("Marked as Delivered"), indicator: "blue" });
					},
				});
			},
		});
		d.show();
	},
});
