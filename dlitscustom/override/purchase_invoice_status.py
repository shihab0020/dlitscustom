import frappe


def on_purchase_invoice_submit(doc, method=None):
	"""When a Purchase Invoice is submitted, update linked Purchase Receipt invoice status."""
	pr_names = {
		row.purchase_receipt
		for row in doc.items
		if row.purchase_receipt
	}

	for pr_name in pr_names:
		per_billed = frappe.db.get_value("Purchase Receipt", pr_name, "per_billed") or 0
		if per_billed >= 100:
			new_status = "Purchase Invoice Completed"
		elif per_billed > 0:
			new_status = "Purchase Invoice Partially Completed"
		else:
			continue
		frappe.db.set_value(
			"Purchase Receipt", pr_name,
			"custom_invoice_status", new_status,
			update_modified=False,
		)
