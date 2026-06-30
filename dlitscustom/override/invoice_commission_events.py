import frappe
from frappe.utils import flt


@frappe.whitelist()
def create_commission_from_form(sales_invoice):
    """Recovery function — creates a commission record for an already-submitted invoice."""
    doc = frappe.get_doc("Sales Invoice", sales_invoice)
    if doc.docstatus != 1 or doc.is_return:
        frappe.throw("Only submitted (non-return) invoices can have a commission created.")
    _create_invoice_commission(doc)
    return frappe.db.get_value("Dlits Invoice Commission", {"sales_invoice": sales_invoice}, "name")


def on_sales_invoice_submit(doc, method=None):
    if doc.is_return:
        _flag_commission_on_return(doc)
    else:
        _create_invoice_commission(doc)


def on_sales_invoice_cancel(doc, method=None):
    if doc.is_return:
        _unflag_commission_on_return_cancel(doc)
    else:
        _cancel_invoice_commission(doc)


# ── helpers ──────────────────────────────────────────────────────────────────

def _create_invoice_commission(doc):
    if not flt(doc.get("dlits_fixed_commission")):
        return
    if frappe.db.exists("Dlits Invoice Commission", {"sales_invoice": doc.name}):
        return

    commission = frappe.get_doc({
        "doctype": "Dlits Invoice Commission",
        "sales_invoice": doc.name,
        "buyer_representative": doc.get("dlits_buyer_representative"),
        "original_commission": flt(doc.get("dlits_fixed_commission")),
        "status": "Pending",
    })
    commission.insert(ignore_permissions=True)

    # Store reference back on the invoice for quick JS lookup
    frappe.db.set_value(
        "Sales Invoice", doc.name,
        "dlits_commission_ref", commission.name,
        update_modified=False,
    )

    frappe.msgprint(
        f"Invoice Commission <b>{commission.name}</b> created for this invoice.",
        indicator="green",
        alert=True,
    )


def _flag_commission_on_return(doc):
    if not doc.return_against:
        return

    commission_name = frappe.db.get_value(
        "Dlits Invoice Commission",
        {"sales_invoice": doc.return_against},
        "name",
    )
    if not commission_name:
        return

    commission = frappe.get_doc("Dlits Invoice Commission", commission_name)
    if commission.status in ("Closed",):
        return

    # Avoid duplicate return review rows
    existing = [r.return_invoice for r in commission.return_reviews]
    if doc.name in existing:
        return

    commission.needs_review = 1
    commission.append("return_reviews", {
        "return_invoice": doc.name,
        "return_date": doc.posting_date,
        "return_amount": abs(flt(doc.grand_total)),
        "review_status": "Pending",
    })

    if commission.status == "Pending":
        commission.status = "Under Review"
    elif commission.status == "Approved":
        commission.status = "Under Review"

    commission.flags.ignore_permissions = True
    commission.save()

    frappe.msgprint(
        f"Commission <b>{commission_name}</b> flagged for manager review due to this return.",
        indicator="orange",
        alert=True,
    )


def _cancel_invoice_commission(doc):
    commission_name = frappe.db.get_value(
        "Dlits Invoice Commission",
        {"sales_invoice": doc.name},
        "name",
    )
    if not commission_name:
        return

    commission = frappe.get_doc("Dlits Invoice Commission", commission_name)
    if commission.status == "Pending":
        frappe.delete_doc("Dlits Invoice Commission", commission_name, ignore_permissions=True)
        frappe.db.set_value(
            "Sales Invoice", doc.name,
            "dlits_commission_ref", None,
            update_modified=False,
        )
    else:
        frappe.throw(
            f"Cannot cancel this invoice. The linked commission record "
            f"<b>{commission_name}</b> is already in <b>{commission.status}</b> status.<br>"
            "Please close or fully settle the commission record first.",
            title="Commission Record Exists",
        )


def _unflag_commission_on_return_cancel(doc):
    if not doc.return_against:
        return

    commission_name = frappe.db.get_value(
        "Dlits Invoice Commission",
        {"sales_invoice": doc.return_against},
        "name",
    )
    if not commission_name:
        return

    commission = frappe.get_doc("Dlits Invoice Commission", commission_name)

    # Remove this return's row from return_reviews
    commission.return_reviews = [
        r for r in commission.return_reviews
        if r.return_invoice != doc.name
    ]

    # If no more pending reviews, clear flag
    has_pending = any(r.review_status == "Pending" for r in commission.return_reviews)
    if not has_pending:
        commission.needs_review = 0
        if commission.status == "Under Review":
            commission.status = "Approved" if commission.approved_by else "Pending"

    commission.flags.ignore_permissions = True
    commission.save()
