import frappe
from frappe.model.document import Document
from frappe.utils import today
from frappe import _


class DlitsStockTransferRequest(Document):
	def before_save(self):
		self._set_title()
		self._auto_fill_technician_warehouse()

	def validate(self):
		self._validate_items()

	def on_submit(self):
		# Supervisor's final action — only allowed when technician has confirmed receipt
		if self.status != "Received":
			frappe.throw(
				_("Cannot submit: the request must reach 'Received' status first. "
				  "Current status: {0}").format(self.status)
			)
		se = _create_stock_entry(self)
		self.db_set("status", "Completed")
		self.db_set("stock_entry", se.name)
		self.db_set("completion_date", today())

	def on_cancel(self):
		if self.stock_entry:
			frappe.throw(
				_("Cannot cancel: Stock Entry {0} has already been created. Cancel it first.").format(
					self.stock_entry
				)
			)
		self.db_set("status", "Cancelled")

	# ── Private helpers ────────────────────────────────────────────────────────

	def _set_title(self):
		tech = self.technician_name or self.requested_by or ""
		self.title = f"{self.request_type} – {tech}"

	def _auto_fill_technician_warehouse(self):
		if self.requested_by and not self.destination_warehouse:
			assignment = _get_user_assignment(self.requested_by)
			if assignment and assignment.get("default_target_warehouse"):
				self.destination_warehouse = assignment["default_target_warehouse"]

	def _validate_items(self):
		if not self.items:
			frappe.throw(_("Please add at least one item to the request."))
		for row in self.items:
			if not row.qty or row.qty <= 0:
				frappe.throw(
					_("Row {0}: Quantity must be greater than 0 for item {1}.").format(
						row.idx, row.item_code
					)
				)


# ─── Module-level helpers ──────────────────────────────────────────────────────

def _get_user_assignment(user):
	return frappe.db.get_value(
		"Dlits Warehouse User Assignment",
		{"user": user, "is_active": 1},
		["default_source_warehouse", "default_target_warehouse", "dlits_role"],
		as_dict=True,
	)


def _create_stock_entry(doc):
	se = frappe.new_doc("Stock Entry")
	se.stock_entry_type = "Material Transfer"
	se.company = doc.company
	se.posting_date = today()
	se.remarks = f"Dlits Stock Transfer Request: {doc.name}"

	for row in doc.items:
		effective_qty = row.received_qty or row.delivered_qty or row.qty
		if not effective_qty or effective_qty <= 0:
			continue

		s_wh = row.from_warehouse or doc.source_warehouse
		t_wh = row.to_warehouse or doc.destination_warehouse

		if doc.request_type == "Return":
			s_wh, t_wh = t_wh, s_wh

		se.append("items", {
			"item_code": row.item_code,
			"qty": effective_qty,
			"uom": row.uom,
			"s_warehouse": s_wh,
			"t_warehouse": t_wh,
		})

	if not se.items:
		frappe.throw(_("No valid items found to transfer."))

	se.insert(ignore_permissions=True)
	se.submit()
	return se


# ─── Document creation from Sales Order / Project ─────────────────────────────

@frappe.whitelist()
def make_stock_transfer_from_so(source_name, target_doc=None):
	"""Called from Sales Order form — returns a new DSTR with items pre-filled."""
	from frappe.model.mapper import get_mapped_doc

	def set_missing_values(source, target):
		target.reference_type = "Sales Order"
		target.request_type = "Transfer"

	return get_mapped_doc(
		"Sales Order",
		source_name,
		{
			"Sales Order": {
				"doctype": "Dlits Stock Transfer Request",
				"field_map": {
					"name": "reference_name",
					"company": "company",
				},
			},
			"Sales Order Item": {
				"doctype": "Dlits Stock Transfer Item",
				"field_map": {
					"item_code": "item_code",
					"item_name": "item_name",
					"qty": "qty",
					"uom": "uom",
					"description": "remarks",
				},
			},
		},
		target_doc,
		set_missing_values,
	)


@frappe.whitelist()
def make_stock_transfer_from_project(project):
	"""Called from Project form — returns a new DSTR linked to the project."""
	project_doc = frappe.get_doc("Project", project)
	doc = frappe.new_doc("Dlits Stock Transfer Request")
	doc.reference_type = "Project"
	doc.reference_name = project
	doc.company = project_doc.company or frappe.defaults.get_global_default("company")
	doc.request_type = "Transfer"
	return doc


@frappe.whitelist()
def get_items_from_sales_order(sales_order):
	"""Fetch item rows from a Sales Order for the 'Get Items' button on the DSTR form."""
	so = frappe.get_doc("Sales Order", sales_order)
	return [
		{
			"item_code": row.item_code,
			"item_name": row.item_name,
			"qty": row.qty,
			"uom": row.uom,
			"remarks": row.description or "",
		}
		for row in so.items
	]


# ─── Whitelisted API ───────────────────────────────────────────────────────────

@frappe.whitelist()
def get_user_warehouse_assignment(user):
	return _get_user_assignment(user) or {}


@frappe.whitelist()
def get_supervisor_users():
	return frappe.db.get_all(
		"Dlits Warehouse User Assignment",
		filters={"dlits_role": "Supervisor", "is_active": 1},
		fields=["user", "full_name"],
	)


@frappe.whitelist()
def get_showroom_users():
	return frappe.db.get_all(
		"Dlits Warehouse User Assignment",
		filters={"dlits_role": "Showroom", "is_active": 1},
		fields=["user", "full_name", "default_source_warehouse"],
	)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_role_user_query(doctype, txt, searchfield, start, page_len, filters):
	dlits_role = (filters or {}).get("dlits_role", "Supervisor")
	assigned_users = frappe.db.get_all(
		"Dlits Warehouse User Assignment",
		filters={"dlits_role": dlits_role, "is_active": 1},
		pluck="user",
	)
	if not assigned_users:
		return []
	return frappe.db.get_all(
		"User",
		filters=[
			["name", "in", assigned_users],
			["name", "like", f"%{txt}%"],
		],
		fields=["name", "full_name"],
		start=start,
		page_length=page_len,
		as_list=True,
	)


@frappe.whitelist()
def request_for_approval(name):
	"""Technician submits request to supervisor. Document stays in Draft."""
	doc = frappe.get_doc("Dlits Stock Transfer Request", name)
	if doc.docstatus != 0:
		frappe.throw(_("Document must be in Draft to request approval."))
	if doc.status not in ("Draft", "Rejected"):
		frappe.throw(_("Request has already been actioned (status: {0}).").format(doc.status))
	if not doc.items:
		frappe.throw(_("Please add items before requesting approval."))

	doc.db_set("status", "Pending Approval")
	_notify_role("Supervisor", f"New Stock Transfer Request {name} needs your approval.")
	return "Pending Approval"


@frappe.whitelist()
def approve_request(name, supervisor_notes=None, source_warehouse=None, assigned_showroom_user=None):
	doc = frappe.get_doc("Dlits Stock Transfer Request", name)
	if doc.status != "Pending Approval":
		frappe.throw(_("Request is not in 'Pending Approval' status."))
	if not source_warehouse:
		frappe.throw(_("Dispatch From Warehouse is required for approval."))
	if not assigned_showroom_user:
		frappe.throw(_("A Showroom User must be assigned before approving."))

	doc.db_set("status", "Approved")
	doc.db_set("assigned_supervisor", frappe.session.user)
	doc.db_set("supervisor_notes", supervisor_notes or "")
	doc.db_set("source_warehouse", source_warehouse)
	doc.db_set("assigned_showroom_user", assigned_showroom_user)
	doc.db_set("approval_date", today())

	frappe.publish_realtime(
		"eval_js",
		f"frappe.show_alert({{message: 'Stock Transfer {name} assigned to you for delivery', indicator: 'green'}})",
		user=assigned_showroom_user,
	)
	return "Approved"


@frappe.whitelist()
def reject_request(name, supervisor_notes=None):
	doc = frappe.get_doc("Dlits Stock Transfer Request", name)
	if doc.status != "Pending Approval":
		frappe.throw(_("Request is not in 'Pending Approval' status."))

	doc.db_set("status", "Rejected")
	doc.db_set("assigned_supervisor", frappe.session.user)
	doc.db_set("supervisor_notes", supervisor_notes or "")
	doc.db_set("approval_date", today())

	frappe.publish_realtime(
		"eval_js",
		f"frappe.show_alert({{message: 'Your Stock Transfer Request {name} was rejected. Check supervisor notes.', indicator: 'red'}})",
		user=doc.requested_by,
	)
	return "Rejected"


@frappe.whitelist()
def mark_delivered(name, showroom_notes=None):
	"""Showroom confirms dispatch. Delivered quantities should already be saved in items."""
	doc = frappe.get_doc("Dlits Stock Transfer Request", name)
	if doc.status != "Approved":
		frappe.throw(_("Request is not in 'Approved' status."))

	# Default delivered_qty = qty for items not explicitly set
	for item in doc.items:
		if not item.delivered_qty:
			frappe.db.set_value(
				"Dlits Stock Transfer Item", item.name, "delivered_qty", item.qty
			)

	doc.db_set("status", "Delivered")
	doc.db_set("showroom_notes", showroom_notes or "")
	doc.db_set("delivery_date", today())

	frappe.publish_realtime(
		"eval_js",
		f"frappe.show_alert({{message: 'Stock transfer {name} dispatched. Please confirm receipt.', indicator: 'blue'}})",
		user=doc.requested_by,
	)
	return "Delivered"


@frappe.whitelist()
def mark_received(name):
	"""Technician confirms receipt. Received quantities should already be saved in items."""
	doc = frappe.get_doc("Dlits Stock Transfer Request", name)
	if doc.status != "Delivered":
		frappe.throw(_("Request is not in 'Delivered' status."))

	for item in doc.items:
		if not item.received_qty:
			frappe.db.set_value(
				"Dlits Stock Transfer Item",
				item.name,
				"received_qty",
				item.delivered_qty or item.qty,
			)

	doc.db_set("status", "Received")
	doc.db_set("received_date", today())

	if doc.assigned_supervisor:
		frappe.publish_realtime(
			"eval_js",
			f"frappe.show_alert({{message: 'Stock transfer {name} received. Ready for your final verification and submit.', indicator: 'purple'}})",
			user=doc.assigned_supervisor,
		)
	return "Received"


def _notify_role(dlits_role, message):
	users = frappe.db.get_all(
		"Dlits Warehouse User Assignment",
		filters={"dlits_role": dlits_role, "is_active": 1},
		pluck="user",
	)
	for user in users:
		frappe.publish_realtime(
			"eval_js",
			f"frappe.show_alert({{message: '{message}', indicator: 'orange'}})",
			user=user,
		)
