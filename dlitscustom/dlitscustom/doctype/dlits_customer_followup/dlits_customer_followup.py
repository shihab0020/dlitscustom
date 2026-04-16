import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, today, get_datetime
from frappe import _

class DlitsCustomerFollowup(Document):
    def validate(self):
        self.calculate_totals()
        self.update_last_contact_date()
        self.calculate_aging()
        self.update_last_outcome()
        self.calculate_linked_totals()

    def calculate_totals(self):
        self.total_interactions = len(self.followup_updates) if self.followup_updates else 0

    def update_last_contact_date(self):
        if self.followup_updates:
            dates = [get_datetime(d.update_date) for d in self.followup_updates if d.update_date]
            if dates:
                self.last_contact_date = max(dates).date()

    def calculate_aging(self):
        self.aging_days = date_diff(today(), self.last_contact_date) if self.last_contact_date else 0

    def update_last_outcome(self):
        """Cache the outcome of the most recent update row that has one set."""
        self.last_outcome = ""
        if self.followup_updates:
            for row in reversed(self.followup_updates):
                if row.outcome:
                    self.last_outcome = row.outcome
                    break

    def calculate_linked_totals(self):
        """Sum balance_amount across all linked document rows."""
        self.total_linked_balance = sum(
            (row.balance_amount or 0) for row in (self.linked_documents or [])
        )

    def on_update(self):
        """Push latest status/date/aging back to the Customer master."""
        if self.customer:
            frappe.db.set_value("Customer", self.customer, {
                "custom_last_followup_status": self.task_status,
                "custom_last_followup_date":   self.last_contact_date,
                "custom_followup_aging":        self.aging_days
            })

    def on_trash(self):
        if not self.customer:
            return
        others = frappe.get_all(
            "Dlits Customer Followup",
            filters={"customer": self.customer, "name": ["!=", self.name]},
            order_by="last_contact_date desc",
            limit=1
        )
        if others:
            frappe.get_doc("Dlits Customer Followup", others[0].name).on_update()
        else:
            frappe.db.set_value("Customer", self.customer, {
                "custom_last_followup_status": "",
                "custom_last_followup_date":   None,
                "custom_followup_aging":        0
            })


# ── Scheduler ─────────────────────────────────────────────────────────────────

def update_customer_aging():
    """Daily: refresh aging_days on all customers that have a followup date."""
    for c in frappe.get_all("Customer", filters={"custom_last_followup_date": ["is", "set"]}):
        last_date = frappe.db.get_value("Customer", c.name, "custom_last_followup_date")
        if last_date:
            frappe.db.set_value(
                "Customer", c.name, "custom_followup_aging",
                date_diff(today(), last_date), update_modified=False
            )


def send_followup_reminders():
    """Daily: email reminders for followups that are due or overdue."""
    active_statuses = [
        "Attempting Contact", "Contacted", "No Response", "Needs Follow-up",
        "Information Sent", "Meeting Scheduled", "Demo Scheduled",
        "Requirement Gathering", "Proposal Preparing", "Proposal Sent",
        "Negotiation", "Waiting Customer Decision"
    ]
    followups = frappe.get_all(
        "Dlits Customer Followup",
        filters={
            "next_followup_date": ["<=", today()],
            "task_status":        ["in", active_statuses]
        },
        fields=["name", "customer", "task_title", "owned_by", "assigned_to",
                "next_followup_date", "is_payment_followup", "total_outstanding"]
    )
    for f in followups:
        recipients = list({f.owned_by, f.assigned_to} - {None, ""})
        payment_line = ""
        if f.is_payment_followup and f.total_outstanding:
            payment_line = _("<br><b>Payment Follow-up</b> — Outstanding: {0}").format(
                frappe.format(f.total_outstanding, {"fieldtype": "Currency"})
            )
        frappe.sendmail(
            recipients=recipients,
            subject=_("Followup Reminder: {0}").format(f.task_title),
            message=_(
                "Pending followup for <b>{0}</b> scheduled on {1}.<br>Task: {2}{3}"
            ).format(f.customer, f.next_followup_date, f.task_title, payment_line),
            reference_doctype="Dlits Customer Followup",
            reference_name=f.name
        )


# ── Whitelisted API ────────────────────────────────────────────────────────────

@frappe.whitelist()
def bulk_update_status(names, status):
    """Bulk-set task_status on multiple followup records."""
    import json
    if isinstance(names, str):
        names = json.loads(names)
    count = 0
    for name in names:
        doc = frappe.get_doc("Dlits Customer Followup", name)
        doc.task_status = status
        doc.save(ignore_permissions=False)
        count += 1
    frappe.db.commit()
    return count


@frappe.whitelist()
def get_customer_outstanding(customer):
    """Return total outstanding Sales Invoice amount for a customer."""
    result = frappe.db.sql("""
        SELECT IFNULL(SUM(outstanding_amount), 0) AS outstanding
        FROM `tabSales Invoice`
        WHERE customer = %s AND docstatus = 1 AND outstanding_amount > 0
    """, customer, as_dict=True)
    return result[0].outstanding if result else 0


@frappe.whitelist()
def get_customer_invoices(customer):
    """Return outstanding invoices for a customer (for payment followup display)."""
    invoices = frappe.db.sql("""
        SELECT
            name, posting_date, due_date,
            grand_total, outstanding_amount,
            DATEDIFF(CURDATE(), IFNULL(due_date, posting_date)) AS overdue_days
        FROM `tabSales Invoice`
        WHERE customer = %s AND docstatus = 1 AND outstanding_amount > 0
        ORDER BY due_date ASC, posting_date ASC
    """, customer, as_dict=True)
    return invoices


@frappe.whitelist()
def get_document_amounts(doctype, docname):
    """Return amount / paid_amount / balance_amount for a linked document."""
    amount = paid_amount = balance_amount = 0
    try:
        if doctype == 'Sales Invoice':
            d = frappe.db.get_value('Sales Invoice', docname,
                ['grand_total', 'outstanding_amount'], as_dict=True)
            if d:
                amount         = d.grand_total or 0
                balance_amount = d.outstanding_amount or 0
                paid_amount    = amount - balance_amount

        elif doctype == 'Sales Order':
            d = frappe.db.get_value('Sales Order', docname,
                ['grand_total', 'advance_paid'], as_dict=True)
            if d:
                amount         = d.grand_total or 0
                paid_amount    = d.advance_paid or 0
                balance_amount = amount - paid_amount

        elif doctype == 'Quotation':
            v = frappe.db.get_value('Quotation', docname, 'grand_total')
            amount = v or 0

        elif doctype == 'Delivery Note':
            v = frappe.db.get_value('Delivery Note', docname, 'grand_total')
            amount = v or 0

        elif doctype == 'Payment Entry':
            v = frappe.db.get_value('Payment Entry', docname, 'paid_amount')
            paid_amount = v or 0
            amount = paid_amount

        elif doctype == 'Opportunity':
            v = frappe.db.get_value('Opportunity', docname, 'opportunity_amount')
            amount = v or 0

    except Exception:
        pass

    return {'amount': amount, 'paid_amount': paid_amount, 'balance_amount': balance_amount}


@frappe.whitelist()
def get_customer_followup_counts(customer):
    """Return followup count summary for a customer (used on Customer form dashboard)."""
    active_statuses = [
        "Attempting Contact", "Contacted", "No Response", "Needs Follow-up",
        "Information Sent", "Meeting Scheduled", "Demo Scheduled",
        "Requirement Gathering", "Proposal Preparing", "Proposal Sent",
        "Negotiation", "Waiting Customer Decision"
    ]
    total = frappe.db.count("Dlits Customer Followup", {"customer": customer})
    active = frappe.db.count("Dlits Customer Followup", {
        "customer": customer,
        "task_status": ["in", active_statuses]
    })
    payment = frappe.db.count("Dlits Customer Followup", {
        "customer": customer,
        "is_payment_followup": 1,
        "task_status": ["not in", ["Completed", "Cancelled", "No Response (Closed)"]]
    })
    overdue = frappe.db.count("Dlits Customer Followup", {
        "customer": customer,
        "next_followup_date": ["<", today()],
        "task_status": ["not in", ["Completed", "Cancelled", "No Response (Closed)"]]
    })
    return {"total": total, "active": active, "payment": payment, "overdue": overdue}


@frappe.whitelist()
def get_followup_summary(customer=None, from_date=None, to_date=None):
    """Aggregate statistics for a set of followups."""
    filters = {}
    if customer:
        filters["customer"] = customer
    if from_date and to_date:
        filters["last_contact_date"] = ["between", [from_date, to_date]]
    elif from_date:
        filters["last_contact_date"] = [">=", from_date]
    elif to_date:
        filters["last_contact_date"] = ["<=", to_date]

    followups = frappe.get_all("Dlits Customer Followup",
        filters=filters,
        fields=["name", "task_status", "priority", "total_interactions"]
    )
    total = len(followups)
    status_count   = {}
    priority_count = {}
    total_updates  = 0
    for f in followups:
        status_count[f.task_status]   = status_count.get(f.task_status, 0) + 1
        priority_count[f.priority]    = priority_count.get(f.priority, 0) + 1
        total_updates                += (f.total_interactions or 0)

    return {
        "total_tasks":              total,
        "total_updates":            total_updates,
        "status_breakdown":         status_count,
        "priority_breakdown":       priority_count,
        "average_updates_per_task": total_updates / total if total else 0
    }
