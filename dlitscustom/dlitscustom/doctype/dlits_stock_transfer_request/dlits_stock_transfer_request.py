import frappe
from frappe.model.document import Document
from frappe.utils import today
from frappe import _


class DlitsStockTransferRequest(Document):
	def before_save(self):
		self._set_title()

	def validate(self):
		self._validate_items()
		self._handle_status_transition()

	def _handle_status_transition(self):
		old = self.get_doc_before_save()
		old_status = old.status if old else None
		new_status = self.status

		if old_status == new_status:
			return

		is_approver = "Shb Stock Transfer Approver" in frappe.get_roles(frappe.session.user)

		if new_status in ("Pending Approval", "Draft"):
			if not is_approver and frappe.session.user != self.requested_by:
				frappe.throw(_("Only the original requester can perform this action."))

		elif new_status in ("Approved", "Rejected"):
			if not self.dispatch_warehouse:
				frappe.throw(_("Please fill <b>Dispatch From Warehouse</b> before approving."))
			if not self.cost_center:
				frappe.throw(_("Please select a <b>Destination Cost Center</b> before approving."))
			if not self.dispatch_users:
				frappe.throw(_("Please add at least one <b>Sending Warehouse User</b> before approving."))
			self.approved_by = frappe.session.user
			self.approval_date = today()

		elif new_status == "Delivered":
			if not is_approver:
				if frappe.session.user == self.requested_by:
					frappe.throw(_("The requester cannot mark as Delivered."))
				allowed = [d.user for d in self.dispatch_users]
				if frappe.session.user not in allowed:
					frappe.throw(_("Only an assigned Sending Warehouse User can mark as Delivered."))
			self.delivery_date = today()

		elif new_status == "Received":
			if not is_approver and frappe.session.user != self.requested_by:
				frappe.throw(_("Only the requester ({0}) can confirm receipt.").format(self.requested_by))
			self.received_date = today()

	def on_submit(self):
		se = _create_stock_entry(self)
		self.db_set("stock_entry", se.name)
		self.db_set("completion_date", today())

	def on_cancel(self):
		if self.stock_entry:
			frappe.throw(
				_("Cannot cancel: Stock Entry {0} already exists. Cancel it first.").format(
					self.stock_entry
				)
			)

	def _set_title(self):
		tech = self.receiver_name or self.requested_by or ""
		self.title = f"{self.request_type} – {tech}"

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


# ─── Stock Entry creation ──────────────────────────────────────────────────────

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

		s_wh = row.from_warehouse or doc.dispatch_warehouse
		t_wh = row.to_warehouse or doc.deliver_to_warehouse

		if doc.request_type == "Return":
			s_wh, t_wh = t_wh, s_wh

		conversion_factor = (
			frappe.db.get_value(
				"UOM Conversion Detail",
				{"parent": row.item_code, "uom": row.uom},
				"conversion_factor",
			) or 1.0
		)

		se.append("items", {
			"item_code": row.item_code,
			"qty": effective_qty,
			"uom": row.uom,
			"conversion_factor": conversion_factor,
			"s_warehouse": s_wh,
			"t_warehouse": t_wh,
			"cost_center": doc.cost_center,
		})

	if not se.items:
		frappe.throw(_("No valid items found to transfer."))

	se.set_missing_values()
	se.insert(ignore_permissions=True)
	se.submit()
	return se


# ─── Document creation from Sales Order / Project ─────────────────────────────

@frappe.whitelist()
def make_stock_transfer_from_so(source_name, target_doc=None):
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
	project_doc = frappe.get_doc("Project", project)
	doc = frappe.new_doc("Dlits Stock Transfer Request")
	doc.reference_type = "Project"
	doc.reference_name = project
	doc.company = project_doc.company or frappe.defaults.get_global_default("company")
	doc.request_type = "Transfer"
	return doc


@frappe.whitelist()
def get_items_from_sales_order(sales_order):
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
