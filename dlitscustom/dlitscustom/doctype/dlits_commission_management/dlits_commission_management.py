import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint


class DlitsCommissionManagement(Document):

    def autoname(self):
        partner_short = (self.sales_partner or "")[:5].strip()
        base = f"{partner_short}-{self.from_date}-{self.to_date}"
        if not frappe.db.exists("Dlits Commission Management", base):
            self.name = base
        else:
            i = 2
            while frappe.db.exists("Dlits Commission Management", f"{base}-{i}"):
                i += 1
            self.name = f"{base}-{i}"

    def validate(self):
        self._check_duplicate_invoices()
        self._recalculate_totals()

    def on_update(self):
        is_group = frappe.db.get_value("Dlits Sales Partner", self.sales_partner, "is_group")
        if is_group:
            frappe.db.sql(
                "UPDATE `tabDlits Commission Invoice` SET is_gp_marked = 1 WHERE parent = %s",
                self.name
            )
        else:
            frappe.db.sql(
                "UPDATE `tabDlits Commission Invoice` SET is_marked = 1 WHERE parent = %s",
                self.name
            )

    def on_submit(self):
        self.db_set("status", "Requested for Approval")

    def on_cancel(self):
        self.db_set("status", "Draft")
        frappe.db.sql(
            "UPDATE `tabDlits Commission Invoice` SET is_marked = 0, is_gp_marked = 0 WHERE parent = %s",
            self.name
        )

    def _check_duplicate_invoices(self):
        if not self.invoices:
            return
        invoice_names = [row.sales_invoice for row in self.invoices if row.sales_invoice]
        if not invoice_names:
            return

        is_group = frappe.db.get_value("Dlits Sales Partner", self.sales_partner, "is_group")
        flag_filter = "dci.is_gp_marked = 1" if is_group else "dci.is_marked = 1"

        placeholders = ", ".join(["%s"] * len(invoice_names))
        duplicates = frappe.db.sql(f"""
            SELECT dci.sales_invoice, dcm.name AS commission_doc
            FROM `tabDlits Commission Invoice` dci
            INNER JOIN `tabDlits Commission Management` dcm ON dcm.name = dci.parent
            WHERE {flag_filter}
              AND dcm.docstatus != 2
              AND dcm.name != %s
              AND dci.sales_invoice IN ({placeholders})
        """, [self.name] + invoice_names, as_dict=True)

        if duplicates:
            lines = ", ".join(
                f"{d.sales_invoice} (in {d.commission_doc})" for d in duplicates
            )
            frappe.throw(
                f"The following invoices are already marked in another Commission doc: {lines}"
            )

    def _recalculate_totals(self):
        total_net = total_gross = total_profit = total_commission = 0
        for row in self.invoices:
            total_net        += flt(row.net_total)
            total_gross      += flt(row.grand_total)
            total_profit     += flt(row.profit)
            total_commission += flt(row.commission_amount)
        self.total_net_amount   = total_net
        self.total_gross_amount = total_gross
        self.total_profit       = total_profit
        self.total_commission   = total_commission

        total_paid = sum(flt(p.amount) for p in (self.payments or []))
        self.total_paid         = total_paid
        self.balance_commission = flt(self.total_commission) - total_paid

        # Auto-mark as Paid once all commission is covered after approval
        if (self.docstatus == 1
                and self.status == "Approved"
                and flt(self.total_commission) > 0
                and flt(self.balance_commission) <= 0):
            self.status = "Paid"


# ---------------------------------------------------------------------------
# Whitelisted function
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_commission_invoices(sales_partner, from_date, to_date, commission_rate,
                             cost_center=None, brand=None, item=None,
                             exclude_unpaid_invoices=1, exclude_partial_invoices=1,
                             exclude_unpaid_returns=1, exclude_partial_returns=1,
                             service_cost_percentage=75, current_doc=None):
    """Return regular invoices + credit notes as separate rows.

    Credit notes carry negative amounts so they naturally reduce totals.
    current_doc: name of the doc being recalculated — excluded from the
    already-marked check so its own previous marks don't block the result.
    """
    is_group = frappe.db.get_value("Dlits Sales Partner", sales_partner, "is_group")

    if is_group:
        return _get_group_invoices(
            sales_partner, from_date, to_date, commission_rate,
            cost_center, brand, item,
            exclude_unpaid_invoices, exclude_partial_invoices,
            exclude_unpaid_returns, exclude_partial_returns,
            service_cost_percentage, current_doc
        )
    else:
        return _get_individual_invoices(
            sales_partner, from_date, to_date, commission_rate,
            cost_center, brand, item,
            exclude_unpaid_invoices, exclude_partial_invoices,
            exclude_unpaid_returns, exclude_partial_returns,
            service_cost_percentage, current_doc
        )


# ---------------------------------------------------------------------------
# Payment filter helpers
# ---------------------------------------------------------------------------

def _invoice_payment_filter(exclude_unpaid, exclude_partial):
    """SQL fragment for regular (positive) invoices."""
    unpaid   = cint(exclude_unpaid)
    partial  = cint(exclude_partial)
    if unpaid and partial:
        return " AND si.outstanding_amount = 0"
    elif unpaid:
        # Exclude fully unpaid; allow partial and fully paid
        return " AND si.outstanding_amount < si.grand_total"
    elif partial:
        # Exclude partial; allow only fully paid or fully unpaid
        return " AND (si.outstanding_amount = 0 OR si.outstanding_amount >= si.grand_total)"
    return ""


def _return_payment_filter(exclude_unpaid, exclude_partial):
    """SQL fragment for credit notes (negative amounts).

    For returns: grand_total < 0, outstanding starts at grand_total (unreconciled)
    and moves toward 0 as it is applied against invoices.
    """
    unpaid   = cint(exclude_unpaid)
    partial  = cint(exclude_partial)
    if unpaid and partial:
        # Only fully reconciled returns (outstanding = 0)
        return " AND si.outstanding_amount = 0"
    elif unpaid:
        # Exclude fully unreconciled (outstanding = grand_total)
        return " AND si.outstanding_amount != si.grand_total"
    elif partial:
        # Exclude partially reconciled; allow only full extremes
        return " AND (si.outstanding_amount = 0 OR si.outstanding_amount = si.grand_total)"
    return ""


# ---------------------------------------------------------------------------
# Duplicate-exclusion clause
# ---------------------------------------------------------------------------

def _exclude_marked_clause(flag, current_doc):
    """SQL fragment: skip invoices already claimed by other commission docs."""
    current_filter = f"AND dcm.name != {frappe.db.escape(current_doc)}" if current_doc else ""
    return f"""
        AND si.name NOT IN (
            SELECT dci.sales_invoice
            FROM `tabDlits Commission Invoice` dci
            INNER JOIN `tabDlits Commission Management` dcm ON dcm.name = dci.parent
            WHERE dci.{flag} = 1
              AND dcm.docstatus != 2
              {current_filter}
        )
    """


# ---------------------------------------------------------------------------
# Enrichment — profit + commission (works with negative amounts for returns)
# ---------------------------------------------------------------------------

def _enrich_invoices(invoices, commission_rate, service_cost_percentage):
    """Attach profit and commission_amount to each invoice dict.

    Credit note rows have negative net_total; their qty in items is also
    negative, so cost and commission come out negative automatically.
    """
    if not invoices:
        return invoices

    from collections import defaultdict

    rate              = flt(commission_rate)
    service_cost_rate = flt(service_cost_percentage) / 100
    invoice_names     = [inv["sales_invoice"] for inv in invoices]
    placeholders      = ", ".join(["%s"] * len(invoice_names))

    items_by_invoice = defaultdict(list)
    for it in frappe.db.sql(f"""
        SELECT parent, net_amount, qty, incoming_rate
        FROM `tabSales Invoice Item`
        WHERE parent IN ({placeholders})
    """, invoice_names, as_dict=True):
        items_by_invoice[it.parent].append(it)

    for inv in invoices:
        net = flt(inv["net_total"])

        total_cost = 0.0
        for it in items_by_invoice.get(inv["sales_invoice"], []):
            if flt(it.incoming_rate) > 0:
                total_cost += flt(it.qty) * flt(it.incoming_rate)
            else:
                total_cost += flt(it.net_amount) * service_cost_rate

        inv["profit"]            = round(net - total_cost, 2)
        inv["commission_amount"] = round(net * rate / 100, 2)

    return invoices


# ---------------------------------------------------------------------------
# Shared SELECT columns
# ---------------------------------------------------------------------------

_SELECT_COLS = """
    si.name                                      AS sales_invoice,
    si.posting_date,
    si.customer,
    si.is_return,
    si.net_total,
    si.grand_total,
    (si.grand_total - si.net_total)              AS tax_amount,
    (si.grand_total - si.outstanding_amount)     AS paid_amount,
    si.outstanding_amount
"""


def _mark_defaults(invoices):
    for inv in invoices:
        inv["is_marked"]    = 0
        inv["is_gp_marked"] = 0
    return invoices


# ---------------------------------------------------------------------------
# Individual partner invoices
# ---------------------------------------------------------------------------

def _get_individual_invoices(sales_partner, from_date, to_date, commission_rate,
                              cost_center, brand, item,
                              exclude_unpaid_invoices, exclude_partial_invoices,
                              exclude_unpaid_returns, exclude_partial_returns,
                              service_cost_percentage, current_doc):
    base_values = {"sales_partner": sales_partner, "from_date": from_date, "to_date": to_date}
    exclude     = _exclude_marked_clause("is_marked", current_doc)
    join, brand_item_filter, extra_values = _build_brand_item_join(brand, item)

    cc_filter = ""
    if cost_center:
        cc_filter = " AND si.cost_center = %(cost_center)s"
        base_values["cost_center"] = cost_center

    values = {**base_values, **extra_values}

    def run(is_return, payment_filter):
        rt = 1 if is_return else 0
        return frappe.db.sql(f"""
            SELECT DISTINCT {_SELECT_COLS}
            FROM `tabSales Invoice` si {join}
            WHERE si.docstatus = 1
              AND si.dlits_sales_partner = %(sales_partner)s
              AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
              AND si.is_return = {rt}
              {cc_filter}
              {payment_filter}
              {exclude}
              {brand_item_filter}
            ORDER BY si.posting_date
        """, values, as_dict=True)

    invoices = (
        run(False, _invoice_payment_filter(exclude_unpaid_invoices, exclude_partial_invoices)) +
        run(True,  _return_payment_filter(exclude_unpaid_returns, exclude_partial_returns))
    )
    invoices.sort(key=lambda x: x["posting_date"] or "")
    return _enrich_invoices(_mark_defaults(invoices), commission_rate, service_cost_percentage)


# ---------------------------------------------------------------------------
# Group partner invoices
# ---------------------------------------------------------------------------

def _get_group_invoices(sales_partner, from_date, to_date, commission_rate,
                         cost_center, brand, item,
                         exclude_unpaid_invoices, exclude_partial_invoices,
                         exclude_unpaid_returns, exclude_partial_returns,
                         service_cost_percentage, current_doc):
    if not cost_center:
        frappe.throw("Cost Center is mandatory for Group commission calculation.")

    base_values = {
        "cost_center": cost_center,
        "from_date": from_date,
        "to_date": to_date,
        "sales_partner": sales_partner,
    }
    exclude = _exclude_marked_clause("is_gp_marked", current_doc)
    join, brand_item_filter, extra_values = _build_brand_item_join(brand, item)
    values = {**base_values, **extra_values}

    def run(is_return, payment_filter):
        rt = 1 if is_return else 0
        return frappe.db.sql(f"""
            SELECT DISTINCT {_SELECT_COLS}
            FROM `tabSales Invoice` si {join}
            WHERE si.docstatus = 1
              AND si.cost_center = %(cost_center)s
              AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
              AND si.is_return = {rt}
              AND (
                  si.dlits_sales_partner IS NULL
                  OR si.dlits_sales_partner = ''
                  OR si.dlits_sales_partner = %(sales_partner)s
                  OR si.dlits_sales_partner IN (
                      SELECT name FROM `tabDlits Sales Partner`
                      WHERE partner_type = 'External' AND is_group = 0
                  )
              )
              {payment_filter}
              {exclude}
              {brand_item_filter}
            ORDER BY si.posting_date
        """, values, as_dict=True)

    invoices = (
        run(False, _invoice_payment_filter(exclude_unpaid_invoices, exclude_partial_invoices)) +
        run(True,  _return_payment_filter(exclude_unpaid_returns, exclude_partial_returns))
    )
    invoices.sort(key=lambda x: x["posting_date"] or "")
    return _enrich_invoices(_mark_defaults(invoices), commission_rate, service_cost_percentage)


# ---------------------------------------------------------------------------
# Brand / item join helper
# ---------------------------------------------------------------------------

def _build_brand_item_join(brand, item):
    if not brand and not item:
        return "", "", {}
    join   = "INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name AND sii.docstatus = 1"
    filter_ = ""
    values  = {}
    if brand:
        filter_ += " AND sii.brand = %(brand)s"
        values["brand"] = brand
    if item:
        filter_ += " AND sii.item_code = %(item)s"
        values["item"] = item
    return join, filter_, values


# ---------------------------------------------------------------------------
# Partner payment info helper
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_partner_payment_info(sales_partner):
    """Return partner type, supplier, and linked employee (if any) for the payment dialog."""
    partner = frappe.db.get_value(
        "Dlits Sales Partner", sales_partner,
        ["partner_type", "supplier", "user", "is_group"],
        as_dict=True
    )
    if not partner:
        return {}

    employee = None
    if partner.partner_type == "Internal User" and partner.user:
        employee = frappe.db.get_value("Employee", {"user_id": partner.user}, "name")

    return {
        "partner_type": partner.partner_type,
        "supplier":     partner.supplier,
        "user":         partner.user,
        "is_group":     partner.is_group,
        "employee":     employee,
    }


# ---------------------------------------------------------------------------
# Additional Salary payment (for internal employee partners)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def create_additional_salary_payment(name, employee, salary_component, payroll_date, amount):
    doc = frappe.get_doc("Dlits Commission Management", name)
    if doc.status != "Approved":
        frappe.throw("Commission must be in 'Approved' status before making a payment.")
    amount = flt(amount)
    if amount <= 0:
        frappe.throw("Payment amount must be greater than zero.")

    company = (frappe.defaults.get_user_default("Company")
               or frappe.db.get_single_value("Global Defaults", "default_company"))

    add_sal = frappe.get_doc({
        "doctype":          "Additional Salary",
        "employee":         employee,
        "salary_component": salary_component,
        "company":          company,
        "payroll_date":     payroll_date,
        "amount":           amount,
        "overwrite_salary_structure_amount": 0,
    })
    add_sal.insert(ignore_permissions=True)
    add_sal.submit()

    doc.reload()
    doc.append("payments", {
        "reference_type":    "Additional Salary",
        "reference_doctype": "Additional Salary",
        "reference_name":    add_sal.name,
        "payment_date":      payroll_date,
        "amount":            amount,
        "remarks":           f"Commission via Additional Salary ({add_sal.name})",
    })
    doc.flags.ignore_permissions = True
    doc.save()

    return add_sal.name


# ---------------------------------------------------------------------------
# Approval workflow
# ---------------------------------------------------------------------------

@frappe.whitelist()
def approve_commission(name):
    if "Shb Commission Approver" not in frappe.get_roles():
        frappe.throw("Only users with the 'Shb Commission Approver' role can approve commissions.")
    doc = frappe.get_doc("Dlits Commission Management", name)
    if doc.docstatus != 1 or doc.status != "Requested for Approval":
        frappe.throw(f"Cannot approve. Status must be 'Requested for Approval' (current: {doc.status}).")
    doc.db_set("status", "Approved")
    doc.db_set("approved_by", frappe.session.user)
    doc.db_set("approved_on", frappe.utils.nowdate())
    frappe.db.commit()


@frappe.whitelist()
def reject_commission(name, rejection_reason=""):
    if "Shb Commission Approver" not in frappe.get_roles():
        frappe.throw("Only users with the 'Shb Commission Approver' role can reject commissions.")
    doc = frappe.get_doc("Dlits Commission Management", name)
    if doc.docstatus != 1 or doc.status not in ("Requested for Approval", "Approved"):
        frappe.throw(f"Cannot reject. Status must be Requested for Approval or Approved (current: {doc.status}).")
    if rejection_reason:
        doc.db_set("rejection_reason", rejection_reason)
        doc.db_set("rejected_by", frappe.session.user)
        frappe.db.commit()
    doc.flags.ignore_permissions = True
    doc.cancel()


# ---------------------------------------------------------------------------
# Commission payment via Journal Entry
# ---------------------------------------------------------------------------

@frappe.whitelist()
def create_payment_journal_entry(name, payment_date, expense_account, payment_account,
                                  amount, cheque_no=None):
    doc = frappe.get_doc("Dlits Commission Management", name)
    if doc.status != "Approved":
        frappe.throw("Commission must be in 'Approved' status before making a payment.")
    amount = flt(amount)
    if amount <= 0:
        frappe.throw("Payment amount must be greater than zero.")

    company = (frappe.defaults.get_user_default("Company")
               or frappe.db.get_single_value("Global Defaults", "default_company"))

    je_dict = {
        "doctype": "Journal Entry",
        "voucher_type": "Journal Entry",
        "company": company,
        "posting_date": payment_date,
        "user_remark": f"Commission Payment: {doc.sales_partner} ({doc.from_date} to {doc.to_date})",
        "accounts": [
            {
                "account": expense_account,
                "debit_in_account_currency": amount,
                "credit_in_account_currency": 0,
                "cost_center": doc.get("cost_center") or None,
                "user_remark": f"Commission — {doc.name}",
            },
            {
                "account": payment_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": amount,
            },
        ],
    }
    if cheque_no:
        je_dict["cheque_no"]   = cheque_no
        je_dict["cheque_date"] = payment_date

    je = frappe.get_doc(je_dict)
    je.insert(ignore_permissions=True)
    je.submit()

    # Record in payments child table and save (triggers _recalculate_totals → auto-Paid)
    doc.reload()
    doc.append("payments", {
        "reference_type":    "Journal Entry",
        "reference_doctype": "Journal Entry",
        "reference_name":    je.name,
        "payment_date":      payment_date,
        "amount":            amount,
        "remarks":           f"Commission JE: {je.name}",
    })
    doc.flags.ignore_permissions = True
    doc.save()

    return je.name
