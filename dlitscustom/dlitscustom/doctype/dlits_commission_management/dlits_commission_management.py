import frappe
from frappe.model.document import Document
from frappe.utils import flt


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
        frappe.db.sql(
            "UPDATE `tabDlits Commission Invoice` SET is_marked = 1 WHERE parent = %s",
            self.name
        )

    def on_submit(self):
        self.db_set("status", "Requested for Approval")

    def on_cancel(self):
        self.db_set("status", "Draft")
        frappe.db.sql(
            "UPDATE `tabDlits Commission Invoice` SET is_marked = 0 WHERE parent = %s",
            self.name
        )

    def _check_duplicate_invoices(self):
        if not self.invoices:
            return
        invoice_names = [row.sales_invoice for row in self.invoices if row.sales_invoice]
        if not invoice_names:
            return
        placeholders = ", ".join(["%s"] * len(invoice_names))
        duplicates = frappe.db.sql(f"""
            SELECT dci.sales_invoice, dcm.name AS commission_doc
            FROM `tabDlits Commission Invoice` dci
            INNER JOIN `tabDlits Commission Management` dcm ON dcm.name = dci.parent
            WHERE dci.is_marked = 1
              AND dcm.docstatus != 2
              AND dcm.name != %s
              AND dci.sales_invoice IN ({placeholders})
        """, [self.name] + invoice_names, as_dict=True)
        if duplicates:
            lines = ", ".join(
                f"{d.sales_invoice} (in {d.commission_doc})" for d in duplicates
            )
            frappe.throw(
                f"The following invoices are already marked in a submitted Commission doc: {lines}"
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


@frappe.whitelist()
def get_commission_invoices(sales_partner, from_date, to_date, commission_rate,
                             cost_center=None, brand=None, item=None,
                             avoid_draft_invoices=1, avoid_non_paid_invoices=1,
                             avoid_partial_paid=1, deduct_return=1,
                             service_cost_percentage=75):
    """Fetch submitted Sales Invoices for the partner within date range, excluding marked ones."""

    values = {
        "sales_partner": sales_partner,
        "from_date": from_date,
        "to_date": to_date,
    }

    join = ""
    extra = ""

    if cost_center:
        extra += " AND si.cost_center = %(cost_center)s"
        values["cost_center"] = cost_center

    if brand or item:
        join = "INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name AND sii.docstatus = 1"
        if brand:
            extra += " AND sii.brand = %(brand)s"
            values["brand"] = brand
        if item:
            extra += " AND sii.item_code = %(item)s"
            values["item"] = item

    if frappe.utils.cint(avoid_non_paid_invoices) and frappe.utils.cint(avoid_partial_paid):
        # Only fully paid invoices (outstanding = 0)
        extra += " AND si.outstanding_amount = 0"
    elif frappe.utils.cint(avoid_non_paid_invoices):
        # Exclude invoices where nothing has been paid
        extra += " AND si.outstanding_amount < si.grand_total"
    elif frappe.utils.cint(avoid_partial_paid):
        # Exclude partially paid — allow only fully paid or fully unpaid
        extra += " AND (si.outstanding_amount = 0 OR si.outstanding_amount >= si.grand_total)"

    # Always exclude credit notes / return invoices themselves
    extra += " AND si.is_return = 0"

    query = f"""
        SELECT DISTINCT
            si.name            AS sales_invoice,
            si.posting_date,
            si.customer,
            si.net_total,
            si.grand_total,
            (si.grand_total - si.net_total)         AS tax_amount,
            (si.grand_total - si.outstanding_amount) AS paid_amount,
            si.outstanding_amount
        FROM `tabSales Invoice` si
        {join}
        WHERE si.docstatus = 1
          AND si.dlits_sales_partner = %(sales_partner)s
          AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
          AND si.name NOT IN (
              SELECT dci.sales_invoice
              FROM `tabDlits Commission Invoice` dci
              INNER JOIN `tabDlits Commission Management` dcm ON dcm.name = dci.parent
              WHERE dci.is_marked = 1 AND dcm.docstatus != 2
          )
          {extra}
        ORDER BY si.posting_date
    """

    invoices = frappe.db.sql(query, values, as_dict=True)
    if not invoices:
        return invoices

    rate = flt(commission_rate)
    service_cost_rate = flt(service_cost_percentage) / 100
    invoice_names = [inv["sales_invoice"] for inv in invoices]
    placeholders = ", ".join(["%s"] * len(invoice_names))

    from collections import defaultdict

    # Fetch return amounts per original invoice
    return_map = defaultdict(float)
    if frappe.utils.cint(deduct_return):
        returns = frappe.db.sql(f"""
            SELECT return_against, ABS(SUM(net_total)) AS return_net
            FROM `tabSales Invoice`
            WHERE is_return = 1 AND docstatus = 1
              AND return_against IN ({placeholders})
            GROUP BY return_against
        """, invoice_names, as_dict=True)
        for r in returns:
            return_map[r.return_against] = flt(r.return_net)

    # Fetch line items for profit estimation
    items = frappe.db.sql(f"""
        SELECT parent, net_amount, qty, incoming_rate
        FROM `tabSales Invoice Item`
        WHERE parent IN ({placeholders})
    """, invoice_names, as_dict=True)
    items_by_invoice = defaultdict(list)
    for it in items:
        items_by_invoice[it.parent].append(it)

    for inv in invoices:
        ret_amt = return_map.get(inv["sales_invoice"], 0)
        effective_net = max(flt(inv["net_total"]) - ret_amt, 0)

        total_cost = 0
        for it in items_by_invoice.get(inv["sales_invoice"], []):
            if flt(it.incoming_rate) > 0:
                total_cost += flt(it.qty) * flt(it.incoming_rate)
            else:
                total_cost += flt(it.net_amount) * service_cost_rate
        # Scale cost proportionally if return deducted
        if flt(inv["net_total"]) > 0:
            cost_ratio = effective_net / flt(inv["net_total"])
            total_cost = total_cost * cost_ratio

        inv["return_amount"] = round(ret_amt, 2)
        inv["profit"] = round(effective_net - total_cost, 2)
        inv["commission_amount"] = round(effective_net * rate / 100, 2)
        inv["is_marked"] = 0

    return invoices
