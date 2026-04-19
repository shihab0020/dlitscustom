import frappe
from erpnext.accounts.report.accounts_receivable_summary.accounts_receivable_summary import (
    AccountsReceivableSummary,
)
from dlitscustom.dlitscustom.report.dlits_accounts_receivable.dlits_accounts_receivable import (
    DlitsReceivableReport,
)


class DlitsReceivableSummary(AccountsReceivableSummary):
    """AR Summary using DlitsReceivableReport so dlits_sales_partner filter is applied."""

    def get_data(self, args):
        # Override to use our subclass instead of bare ReceivablePayableReport
        self.receivables = DlitsReceivableReport(self.filters).run(args)[1]
        from frappe.utils import flt
        from erpnext.accounts.utils import get_currency_precision
        self.currency_precision = get_currency_precision() or 2
        self.get_party_total(args)

        from erpnext.accounts.party import get_partywise_advanced_payment_amount
        party = None
        from frappe import scrub
        for party_type in self.party_type:
            if self.filters.get(scrub(party_type)):
                party = self.filters.get(scrub(party_type))

        party_advance_amount = (
            get_partywise_advanced_payment_amount(
                self.party_type,
                self.filters.report_date,
                self.filters.show_future_payments,
                self.filters.company,
                party=party,
            )
            or {}
        )

        if self.filters.show_gl_balance:
            from erpnext.accounts.report.accounts_receivable_summary.accounts_receivable_summary import (
                get_gl_balance,
            )
            gl_balance_map = get_gl_balance(
                self.filters.report_date, self.filters.company, self.account_type
            )

        self.data = []
        for party, party_dict in self.party_total.items():
            if flt(party_dict.outstanding, self.currency_precision) == 0:
                continue
            row = frappe._dict()
            row.party = party
            if self.party_naming_by == "Naming Series":
                row.party_name = frappe.get_cached_value("Customer", party, "customer_name")
            row.update(party_dict)
            row.advance = party_advance_amount.get(party, 0)
            row.paid -= row.advance
            if self.filters.show_gl_balance:
                row.gl_balance = gl_balance_map.get(party)
                row.diff = flt(row.outstanding) - flt(row.gl_balance)
            if self.filters.show_future_payments:
                row.remaining_balance = flt(row.outstanding) - flt(row.future_amount)
            self.data.append(row)


def execute(filters=None):
    args = {
        "account_type": "Receivable",
        "naming_by": ["Selling Settings", "cust_master_name"],
    }
    return DlitsReceivableSummary(filters).run(args)
