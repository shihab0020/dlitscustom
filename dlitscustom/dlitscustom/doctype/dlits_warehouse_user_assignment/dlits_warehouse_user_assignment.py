import frappe
from frappe.model.document import Document
from frappe import _


class DlitsWarehouseUserAssignment(Document):
	def validate(self):
		if self.dlits_role == "Showroom" and not self.default_source_warehouse:
			frappe.msgprint(
				_("Tip: Set a Default Source Warehouse for Showroom users so it auto-fills on approval."),
				alert=True,
			)
		if self.dlits_role == "Technician" and not self.default_target_warehouse:
			frappe.msgprint(
				_("Tip: Set a Default Target Warehouse for Technician users so it auto-fills on new requests."),
				alert=True,
			)
