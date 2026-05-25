import frappe
from frappe import _


def prevent_duplicate_bill_no(doc, method=None):
	"""Block submission if Supplier Invoice No already exists on another submitted Purchase Invoice."""
	if not doc.bill_no:
		return

	existing = frappe.db.get_value(
		"Purchase Invoice",
		{"bill_no": doc.bill_no, "name": ("!=", doc.name), "docstatus": 1},
		["name", "supplier"],
		as_dict=True,
	)

	if existing:
		frappe.throw(
			_("Supplier Invoice No <b>{0}</b> already exists in Purchase Invoice"
			  " <a href='/app/purchase-invoice/{1}'><b>{1}</b></a> (Supplier: {2})."
			  " Please verify before submitting.").format(
				doc.bill_no, existing.name, existing.supplier
			)
		)
