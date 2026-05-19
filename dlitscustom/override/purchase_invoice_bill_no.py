import frappe


def auto_suffix_duplicate_bill_no(doc, method=None):
	"""If bill_no already exists on another Purchase Invoice, append -1, -2, etc."""
	if not doc.bill_no:
		return

	counter = 1
	original = doc.bill_no

	while frappe.db.exists(
		"Purchase Invoice",
		{"bill_no": doc.bill_no, "name": ("!=", doc.name), "docstatus": ("!=", 2)},
	):
		doc.bill_no = f"{original}-{counter}"
		counter += 1
