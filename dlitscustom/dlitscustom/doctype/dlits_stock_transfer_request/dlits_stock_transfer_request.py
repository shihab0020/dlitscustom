import frappe
from frappe.model.document import Document
from frappe.utils import today
from frappe import _


class DlitsStockTransferRequest(Document):
	def before_save(self):
		self._set_title()
		self._update_qty_totals()

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
			_warn_qty_mismatch(
				self.items,
				check_field="delivered_qty",
				base_field="qty",
				check_label=_("Delivered Qty"),
				base_label=_("Requested Qty"),
			)

		elif new_status == "Received":
			if not is_approver and frappe.session.user != self.requested_by:
				frappe.throw(_("Only the requester ({0}) can confirm receipt.").format(self.requested_by))
			self.received_date = today()

	def before_submit(self):
		missing = [
			f"Row {row.idx} – {row.item_code}"
			for row in self.items
			if not row.delivered_qty or row.delivered_qty <= 0
		]
		if missing:
			frappe.throw(
				_("Cannot submit: Delivered Qty must be filled for all items before submitting.<br><br>{0}").format(
					"<br>".join(missing)
				),
				title=_("Missing Delivered Qty"),
			)
		_warn_submit_quantities(self)

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

	def _update_qty_totals(self):
		self.total_qty = sum(r.qty or 0 for r in self.items)
		self.total_delivered_qty = sum(r.delivered_qty or 0 for r in self.items)

		tq = self.total_qty or 0
		td = self.total_delivered_qty or 0

		if self.status in ("Delivered", "Received", "Completed"):
			self.qty_status = "All Delivered" if (tq and td >= tq) else ("Partial Delivered" if td > 0 else "")
		else:
			self.qty_status = ""

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


# ─── Qty helpers ──────────────────────────────────────────────────────────────

def _get_effective_qty(row):
	"""Return the qty that will be transferred — always delivered_qty."""
	return row.delivered_qty or 0


def _warn_qty_mismatch(items, check_field, base_field, check_label, base_label):
	"""Show an orange warning if any row has a filled check_field that differs from base_field."""
	rows = []
	for row in items:
		check_val = getattr(row, check_field) or 0
		if not check_val:
			continue
		base_val = getattr(row, base_field) or 0
		if check_val != base_val:
			rows.append(
				f"<b>Row {row.idx} – {row.item_code}:</b> "
				f"{base_label} = {base_val} &nbsp;→&nbsp; {check_label} = <b>{check_val}</b>"
			)
	if rows:
		frappe.msgprint(
			_("Quantity mismatch detected — please review before proceeding:<br><br>{0}").format(
				"<br>".join(rows)
			),
			title=_("Qty Mismatch"),
			indicator="orange",
		)


def _warn_submit_quantities(doc):
	"""Before submit: show a summary of the exact quantities that will be transferred."""
	has_mismatch = False
	rows = []
	for row in doc.items:
		effective = _get_effective_qty(row)
		mismatch = effective != row.qty
		if mismatch:
			has_mismatch = True
		label = (
			f"<b>Row {row.idx} – {row.item_code}:</b> "
			f"Requested {row.qty} → "
			f"<b style='color:{'orange' if mismatch else 'green'}'>"
			f"Will transfer {effective} {row.uom or ''}</b>"
		)
		rows.append(label)

	indicator = "orange" if has_mismatch else "blue"
	note = (
		_("<br><br><b>⚠ Some quantities differ from the original request.</b>")
		if has_mismatch else ""
	)
	frappe.msgprint(
		_("Stock Entry will be created with the following quantities:<br><br>{0}{1}").format(
			"<br>".join(rows), note
		),
		title=_("Confirm Transfer Quantities"),
		indicator=indicator,
	)


# ─── Stock Entry creation ──────────────────────────────────────────────────────

def _create_stock_entry(doc):
	se = frappe.new_doc("Stock Entry")
	se.stock_entry_type = "Material Transfer"
	se.company = doc.company
	se.posting_date = today()
	se.remarks = f"Dlits Stock Transfer Request: {doc.name} [{doc.request_type}]"

	s_wh = doc.dispatch_warehouse
	t_wh = doc.deliver_to_warehouse

	for row in doc.items:
		effective_qty = _get_effective_qty(row)
		if not effective_qty or effective_qty <= 0:
			continue

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

	# Restore warehouses — set_missing_values() may overwrite them with item defaults
	for item in se.items:
		item.s_warehouse = s_wh
		item.t_warehouse = t_wh

	se.custom_dlitsstocktransferrequest = doc.name
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
					"description": "description",
					"qty": "qty",
					"uom": "uom",
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
			"description": row.description or "",
			"qty": row.qty,
			"uom": row.uom,
		}
		for row in so.items
	]
