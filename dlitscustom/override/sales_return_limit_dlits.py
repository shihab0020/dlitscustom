import frappe
from frappe.utils import flt


def sales_return_limit_dlits(doc, method=None):
    if not doc.get("is_return") or not doc.get("return_against"):
        return

    _check_return_items_valid(doc)      # only items from original invoice allowed
    _check_buyer_rep_commission(doc)    # buyer rep commission must be settled first
    _check_paid_commission(doc)         # monthly commission protection
    _check_return_limit(doc)            # total return must not exceed original amount


# ── 1. Item validation ───────────────────────────────────────────────────────

def _check_return_items_valid(doc):
    """Block any return item that was not in the original invoice."""
    original_item_codes = {
        row[0] for row in frappe.db.sql(
            "SELECT item_code FROM `tabSales Invoice Item` WHERE parent = %s",
            doc.return_against
        )
    }

    invalid = [
        item.item_code
        for item in doc.items
        if item.item_code not in original_item_codes
    ]

    if invalid:
        frappe.throw(
            f"Sales return on <b>{doc.return_against}</b> can only include items "
            f"that were in the original invoice.<br><br>"
            f"The following items are <b>not</b> in the original invoice:<br>"
            + "<br>".join(f"&nbsp;&nbsp;• {i}" for i in invalid)
            + "<br><br>Remove them before saving.",
            title="Invalid Return Items"
        )


# ── 2. Buyer Representative Commission check ─────────────────────────────────

def _check_buyer_rep_commission(doc):
    """Block or warn when returning an invoice that has a Buyer Rep Commission."""
    commission_name = frappe.db.get_value(
        "Dlits Invoice Commission",
        {"sales_invoice": doc.return_against},
        "name",
    )
    if not commission_name:
        return

    status = frappe.db.get_value("Dlits Invoice Commission", commission_name, "status")
    is_approver = "Shb Commission Approver" in frappe.get_roles()

    if status == "Closed":
        # Commission fully settled — return is allowed
        return

    if status == "Paid":
        if not is_approver:
            frappe.throw(
                f"Invoice <b>{doc.return_against}</b> has a <b>fully paid</b> "
                f"Buyer Representative Commission (<b>{commission_name}</b>).<br><br>"
                f"A Commission Approver must first close the commission record "
                f"(and handle any recovery) before a return can be created.<br><br>"
                f"Steps: Open <b>{commission_name}</b> → decide if the paid commission "
                f"should be recovered → click <b>Close Commission</b> → then retry the return.",
                title="Buyer Commission Paid — Action Required"
            )
        else:
            frappe.msgprint(
                f"⚠ Invoice <b>{doc.return_against}</b> has a <b>Paid</b> Buyer Commission "
                f"<b>{commission_name}</b>.<br>"
                f"Proceeding as Commission Approver. The commission record will be flagged — "
                f"review and update the deduction if needed.",
                indicator="orange",
                title="Buyer Commission Paid — Review Required"
            )

    elif status in ("Approved", "Partially Paid"):
        if not is_approver:
            frappe.throw(
                f"Invoice <b>{doc.return_against}</b> has a Buyer Representative Commission "
                f"(<b>{commission_name}</b>) currently in <b>{status}</b> status.<br><br>"
                f"Only a <b>Commission Approver</b> can create a return while the commission "
                f"is being paid. The approver will then review whether the commission amount "
                f"should be reduced.",
                title="Buyer Commission Active — Approver Required"
            )
        else:
            frappe.msgprint(
                f"⚠ Invoice <b>{doc.return_against}</b> has a Buyer Commission "
                f"<b>{commission_name}</b> in <b>{status}</b> status.<br>"
                f"Proceeding as Commission Approver. The commission record will be flagged for review.",
                indicator="orange",
                title="Buyer Commission Active"
            )

    elif status in ("Pending", "Under Review"):
        # Not yet approved — just notify. The on_submit hook will flag it automatically.
        frappe.msgprint(
            f"Note: Invoice <b>{doc.return_against}</b> has a Buyer Representative Commission "
            f"<b>{commission_name}</b> in <b>{status}</b> status.<br>"
            f"When this return is submitted, the commission record will be automatically "
            f"flagged for manager review before payment.",
            indicator="blue",
            title="Buyer Commission Will Be Flagged"
        )


# ── 3. Monthly commission (paid via Dlits Commission Management) ──────────────

def _check_paid_commission(doc):
    paid = frappe.db.sql("""
        SELECT dcm.name
        FROM `tabDlits Commission Management` dcm
        INNER JOIN `tabDlits Commission Invoice` dci ON dci.parent = dcm.name
        WHERE dci.sales_invoice = %s
          AND dcm.status = 'Paid'
          AND dcm.docstatus = 1
        LIMIT 1
    """, doc.return_against, as_dict=True)

    if not paid:
        return

    commission_doc = paid[0].name
    if "Shb Commission Approver" not in frappe.get_roles():
        frappe.throw(
            f"Invoice <b>{doc.return_against}</b> is part of paid monthly commission "
            f"<b>{commission_doc}</b>.<br>"
            f"Only a <b>Commission Approver</b> can create returns against paid-commission invoices.",
            title="Monthly Commission Paid — Approver Required"
        )
    else:
        frappe.msgprint(
            f"⚠ Invoice <b>{doc.return_against}</b> is in paid monthly commission "
            f"<b>{commission_doc}</b>. Proceeding as Commission Approver.",
            indicator="orange",
            title="Monthly Commission Paid"
        )


# ── 4. Return amount limit ───────────────────────────────────────────────────

def _check_return_limit(doc):
    original_grand_total = flt(
        frappe.db.get_value("Sales Invoice", doc.return_against, "grand_total")
    )
    if not original_grand_total:
        return

    result = frappe.db.sql("""
        SELECT COALESCE(SUM(ABS(grand_total)), 0) AS total_returned
        FROM `tabSales Invoice`
        WHERE is_return = 1
          AND return_against = %s
          AND docstatus != 2
          AND name != %s
    """, (doc.return_against, doc.name or ""), as_dict=True)

    already_returned = flt(result[0].total_returned if result else 0)
    current_return   = abs(flt(doc.grand_total))
    total_return     = already_returned + current_return

    if total_return > original_grand_total:
        remaining = max(0, original_grand_total - already_returned)
        frappe.throw(
            f"Return amount exceeds original invoice <b>{doc.return_against}</b>.<br><br>"
            f"Original Invoice Total: <b>{original_grand_total:,.2f}</b><br>"
            f"Already Returned: <b>{already_returned:,.2f}</b><br>"
            f"This Return: <b>{current_return:,.2f}</b><br>"
            f"Maximum Allowed: <b>{remaining:,.2f}</b>",
            title="Sales Return Limit Exceeded"
        )
