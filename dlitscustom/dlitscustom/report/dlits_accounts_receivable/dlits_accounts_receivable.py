import frappe
from frappe import qb
from erpnext.accounts.report.accounts_receivable.accounts_receivable import ReceivablePayableReport


class DlitsReceivableReport(ReceivablePayableReport):
    """Extends ERPNext AR report to support Dlits Sales Partner filter."""

    def add_customer_filters(self, *args, **kwargs):
        super().add_customer_filters(*args, **kwargs)
        if self.filters.get("dlits_sales_partner"):
            si = qb.DocType("Sales Invoice")
            self.qb_selection_filter.append(
                self.ple.against_voucher_no.isin(
                    qb.from_(si)
                    .select(si.name)
                    .where(si.dlits_sales_partner == self.filters.get("dlits_sales_partner"))
                    .where(si.docstatus == 1)
                )
            )


def execute(filters=None):
    args = {
        "account_type": "Receivable",
        "naming_by": ["Selling Settings", "cust_master_name"],
    }
    return DlitsReceivableReport(filters).run(args)
