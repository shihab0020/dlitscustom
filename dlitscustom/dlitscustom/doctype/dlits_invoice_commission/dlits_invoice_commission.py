import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate, now_datetime


class DlitsInvoiceCommission(Document):

    def validate(self):
        self._recalculate()

    def _recalculate(self):
        self.final_commission = flt(self.original_commission) - flt(self.deduction_approved)
        self.paid_amount = sum(flt(p.amount) for p in (self.payments or []))
        self.recoverable = max(0.0, self.paid_amount - self.final_commission)
        self.balance = max(0.0, self.final_commission - self.paid_amount)

        if self.status == "Closed":
            return
        if flt(self.final_commission) <= 0 and flt(self.deduction_approved) > 0:
            self.status = "Closed"
        elif self.paid_amount > 0 and self.balance <= 0:
            self.status = "Paid"
        elif self.paid_amount > 0 and self.balance > 0:
            self.status = "Partially Paid"


# ── Approval ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def approve_invoice_commission(name, deduction=0, remarks=""):
    if "Shb Commission Approver" not in frappe.get_roles():
        frappe.throw("Only a Commission Approver can approve invoice commissions.")

    doc = frappe.get_doc("Dlits Invoice Commission", name)
    if doc.status not in ("Pending", "Under Review"):
        frappe.throw(f"Cannot approve. Current status is '{doc.status}'.")

    old_deduction = flt(doc.deduction_approved)
    doc.deduction_approved = flt(deduction)
    doc.approved_by = frappe.session.user
    doc.approval_date = nowdate()
    doc.needs_review = 0

    # Mark all pending return reviews as reviewed
    for row in doc.return_reviews:
        if row.review_status == "Pending":
            row.review_status = "Reviewed"
            row.reviewed_by = frappe.session.user
            row.review_date = nowdate()

    doc.append("decision_log", {
        "action_date": now_datetime(),
        "action_by": frappe.session.user,
        "action": "Approved",
        "previous_deduction": old_deduction,
        "new_deduction": flt(deduction),
        "remarks": remarks,
    })

    doc.flags.ignore_permissions = True
    doc.save()
    frappe.db.commit()
    return doc.status


@frappe.whitelist()
def update_deduction(name, deduction, remarks=""):
    if "Shb Commission Approver" not in frappe.get_roles():
        frappe.throw("Only a Commission Approver can update the deduction.")

    doc = frappe.get_doc("Dlits Invoice Commission", name)
    if doc.status not in ("Approved", "Partially Paid"):
        frappe.throw(f"Cannot update deduction. Current status is '{doc.status}'.")

    old_deduction = flt(doc.deduction_approved)
    doc.deduction_approved = flt(deduction)

    doc.append("decision_log", {
        "action_date": now_datetime(),
        "action_by": frappe.session.user,
        "action": "Deduction Updated",
        "previous_deduction": old_deduction,
        "new_deduction": flt(deduction),
        "remarks": remarks,
    })

    doc.flags.ignore_permissions = True
    doc.save()
    frappe.db.commit()
    return doc.status


@frappe.whitelist()
def close_commission(name, remarks=""):
    if "Shb Commission Approver" not in frappe.get_roles():
        frappe.throw("Only a Commission Approver can close commissions.")

    doc = frappe.get_doc("Dlits Invoice Commission", name)
    if doc.status not in ("Paid", "Approved", "Partially Paid"):
        frappe.throw(f"Cannot close. Current status is '{doc.status}'.")

    doc.append("decision_log", {
        "action_date": now_datetime(),
        "action_by": frappe.session.user,
        "action": "Closed",
        "previous_deduction": flt(doc.deduction_approved),
        "new_deduction": flt(doc.deduction_approved),
        "remarks": remarks,
    })

    doc.status = "Closed"
    doc.flags.ignore_permissions = True
    doc.save()
    frappe.db.commit()
    return "Closed"


# ── Payment ──────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_invoice_commission_partner_info(name):
    doc = frappe.get_doc("Dlits Invoice Commission", name)
    if not doc.buyer_representative:
        return {"partner_type": None, "employee": None}

    partner = frappe.db.get_value(
        "Dlits Sales Partner",
        doc.buyer_representative,
        ["partner_type", "user", "is_group"],
        as_dict=True,
    )
    if not partner:
        return {"partner_type": None, "employee": None}

    employee = None
    if partner.partner_type == "Internal User" and partner.user:
        employee = frappe.db.get_value("Employee", {"user_id": partner.user}, "name")

    return {
        "partner_type": partner.partner_type,
        "user": partner.user,
        "is_group": partner.is_group,
        "employee": employee,
    }


@frappe.whitelist()
def create_payment_additional_salary(name, employee, salary_component, payroll_date, amount):
    doc = frappe.get_doc("Dlits Invoice Commission", name)
    if doc.status not in ("Approved", "Partially Paid"):
        frappe.throw("Commission must be 'Approved' before recording a payment.")

    company = (
        frappe.defaults.get_user_default("Company")
        or frappe.db.get_single_value("Global Defaults", "default_company")
    )

    add_sal = frappe.get_doc({
        "doctype": "Additional Salary",
        "employee": employee,
        "salary_component": salary_component,
        "company": company,
        "payroll_date": payroll_date,
        "amount": flt(amount),
        "overwrite_salary_structure_amount": 0,
    })
    add_sal.insert(ignore_permissions=True)
    add_sal.submit()

    doc.reload()
    doc.append("payments", {
        "reference_type": "Additional Salary",
        "reference_name": add_sal.name,
        "payment_date": payroll_date,
        "amount": flt(amount),
        "remarks": f"Commission via Additional Salary ({add_sal.name})",
    })
    doc.append("decision_log", {
        "action_date": now_datetime(),
        "action_by": frappe.session.user,
        "action": "Payment Recorded",
        "amount": flt(amount),
        "remarks": f"Additional Salary: {add_sal.name}",
    })
    doc.flags.ignore_permissions = True
    doc.save()
    frappe.db.commit()
    return add_sal.name


@frappe.whitelist()
def create_payment_journal_entry(name, payment_date, expense_account, payment_account, amount, cheque_no=None):
    doc = frappe.get_doc("Dlits Invoice Commission", name)
    if doc.status not in ("Approved", "Partially Paid"):
        frappe.throw("Commission must be 'Approved' before recording a payment.")

    company = (
        frappe.defaults.get_user_default("Company")
        or frappe.db.get_single_value("Global Defaults", "default_company")
    )

    je_dict = {
        "doctype": "Journal Entry",
        "voucher_type": "Journal Entry",
        "company": company,
        "posting_date": payment_date,
        "user_remark": f"Invoice Commission Payment: {doc.name} ({doc.sales_invoice})",
        "accounts": [
            {
                "account": expense_account,
                "debit_in_account_currency": flt(amount),
                "credit_in_account_currency": 0,
                "user_remark": f"Commission — {doc.name}",
            },
            {
                "account": payment_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": flt(amount),
            },
        ],
    }
    if cheque_no:
        je_dict["cheque_no"] = cheque_no
        je_dict["cheque_date"] = payment_date

    je = frappe.get_doc(je_dict)
    je.insert(ignore_permissions=True)
    je.submit()

    doc.reload()
    doc.append("payments", {
        "reference_type": "Journal Entry",
        "reference_name": je.name,
        "payment_date": payment_date,
        "amount": flt(amount),
        "remarks": f"Commission JE: {je.name}",
    })
    doc.append("decision_log", {
        "action_date": now_datetime(),
        "action_by": frappe.session.user,
        "action": "Payment Recorded",
        "amount": flt(amount),
        "remarks": f"Journal Entry: {je.name}",
    })
    doc.flags.ignore_permissions = True
    doc.save()
    frappe.db.commit()
    return je.name
