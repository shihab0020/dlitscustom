# Copyright (c) 2026, DLITS and contributors
# For license information, please see license.txt

import frappe
from frappe import _, scrub
from frappe.utils import add_days, add_to_date, getdate, today


def execute(filters=None):
    return FollowupReport(filters).run()


class FollowupReport:
    def __init__(self, filters=None):
        self.filters = frappe._dict(filters or {})
        self.filters.setdefault("range", "Monthly")
        self.filters.setdefault("group_by", "Owner")
        self.months = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]
        self.get_period_date_ranges()

    def run(self):
        self.get_columns()
        self.fetch_entries()
        self.build_rows()
        self.get_chart_data()
        self.get_summary()
        return self.columns, self.data, None, self.chart, self.summary, 0

    # ── Columns ───────────────────────────────────────────────────────────────

    def get_columns(self):
        group_by = self.filters.group_by
        label_map = {
            "Owner":    _("Owner"),
            "Customer": _("Customer"),
            "Status":   _("Status"),
            "Priority": _("Priority"),
        }
        self.columns = [
            {
                "label":     label_map.get(group_by, _(group_by)),
                "fieldname": "entity",
                "fieldtype": "Data",
                "width":     200,
            }
        ]
        for end_date in self.periodic_daterange:
            period = self.get_period(end_date)
            self.columns.append({
                "label":     _(period),
                "fieldname": scrub(period),
                "fieldtype": "Int",
                "width":     100,
            })
        self.columns.append({
            "label":     _("Total"),
            "fieldname": "total",
            "fieldtype": "Int",
            "width":     100,
        })

    # ── Data fetch ────────────────────────────────────────────────────────────

    def fetch_entries(self):
        entity_field = self._get_entity_field()
        filters = {
            "last_contact_date": ["between", [self.filters.from_date, self.filters.to_date]]
        }
        if self.filters.get("customer"):
            filters["customer"] = self.filters.customer
        if self.filters.get("task_owner"):
            filters["owned_by"] = self.filters.task_owner
        if self.filters.get("task_status"):
            filters["task_status"] = self.filters.task_status
        if self.filters.get("priority"):
            filters["priority"] = self.filters.priority
        if self.filters.get("is_payment_followup"):
            filters["is_payment_followup"] = 1

        self.entries = frappe.get_all(
            "Dlits Customer Followup",
            filters=filters,
            fields=[entity_field + " as entity", "last_contact_date"],
        )

    def _get_entity_field(self):
        return {
            "Owner":    "owned_by",
            "Customer": "customer",
            "Status":   "task_status",
            "Priority": "priority",
        }.get(self.filters.group_by, "owned_by")

    # ── Row builder ───────────────────────────────────────────────────────────

    def build_rows(self):
        entity_periodic_data = frappe._dict()

        for d in self.entries:
            if not d.last_contact_date:
                continue
            entity = d.entity or _("(Not Set)")
            period = self.get_period(getdate(d.last_contact_date))
            entity_periodic_data.setdefault(entity, frappe._dict())
            entity_periodic_data[entity][period] = entity_periodic_data[entity].get(period, 0) + 1

        self.entity_periodic_data = entity_periodic_data
        self.data = []

        for entity, period_data in entity_periodic_data.items():
            row = {"entity": entity}
            total = 0
            for end_date in self.periodic_daterange:
                period = self.get_period(end_date)
                count = period_data.get(period, 0)
                row[scrub(period)] = count
                total += count
            row["total"] = total
            self.data.append(row)

        self.data.sort(key=lambda x: x["total"], reverse=True)

    # ── Chart ─────────────────────────────────────────────────────────────────

    def get_chart_data(self):
        labels = [self.get_period(d) for d in self.periodic_daterange]

        # Always build a "Total" aggregate line
        totals = []
        for end_date in self.periodic_daterange:
            period = self.get_period(end_date)
            totals.append(sum(row.get(scrub(period), 0) for row in self.data))

        if len(self.data) <= 1:
            # Single entity or empty — show only total
            datasets = [{"name": _("Total"), "values": totals}]
        else:
            # Show top 5 entities individually
            datasets = []
            for row in self.data[:5]:
                datasets.append({
                    "name": row["entity"],
                    "values": [
                        row.get(scrub(self.get_period(d)), 0)
                        for d in self.periodic_daterange
                    ],
                })
            # Append total as a reference line
            datasets.append({"name": _("Total"), "values": totals})

        self.chart = {
            "data":      {"labels": labels, "datasets": datasets},
            "type":      "bar",
            "fieldtype": "Int",
        }

    # ── Summary cards ─────────────────────────────────────────────────────────

    def get_summary(self):
        base = {
            "last_contact_date": ["between", [self.filters.from_date, self.filters.to_date]]
        }
        if self.filters.get("customer"):
            base["customer"] = self.filters.customer
        if self.filters.get("task_owner"):
            base["owned_by"] = self.filters.task_owner
        if self.filters.get("priority"):
            base["priority"] = self.filters.priority
        if self.filters.get("is_payment_followup"):
            base["is_payment_followup"] = 1

        active_statuses = [
            "Attempting Contact", "Contacted", "No Response", "Needs Follow-up",
            "Information Sent", "Meeting Scheduled", "Demo Scheduled",
            "Requirement Gathering", "Proposal Preparing", "Proposal Sent",
            "Negotiation", "Waiting Customer Decision",
        ]
        closed_statuses = ["Completed", "Cancelled", "No Response (Closed)"]

        total   = frappe.db.count("Dlits Customer Followup", base)
        active  = frappe.db.count("Dlits Customer Followup", {**base, "task_status": ["in", active_statuses]})
        payment = frappe.db.count("Dlits Customer Followup", {**base, "is_payment_followup": 1})

        # Overdue: not filtered by last_contact_date — count ALL open followups
        # past their next_followup_date regardless of when they were last contacted.
        # Overdue = active followups with a past next_followup_date
        #           OR no next_followup_date at all (unscheduled → also needs attention)
        extra_conds = ""
        extra_vals  = {"today": today(), "closed": tuple(closed_statuses)}
        if self.filters.get("customer"):
            extra_conds += " AND customer = %(customer)s"
            extra_vals["customer"] = self.filters.customer
        if self.filters.get("task_owner"):
            extra_conds += " AND owned_by = %(task_owner)s"
            extra_vals["task_owner"] = self.filters.task_owner
        if self.filters.get("priority"):
            extra_conds += " AND priority = %(priority)s"
            extra_vals["priority"] = self.filters.priority
        if self.filters.get("is_payment_followup"):
            extra_conds += " AND is_payment_followup = 1"

        overdue = frappe.db.sql(f"""
            SELECT COUNT(*) FROM `tabDlits Customer Followup`
            WHERE task_status NOT IN %(closed)s
              AND (next_followup_date < %(today)s OR next_followup_date IS NULL)
              {extra_conds}
        """, extra_vals)[0][0]

        self.summary = [
            {"label": _("Total Followups"), "value": total,   "indicator": "gray",   "datatype": "Int"},
            {"label": _("Active"),          "value": active,  "indicator": "blue",   "datatype": "Int"},
            {"label": _("Payment"),         "value": payment, "indicator": "orange", "datatype": "Int"},
            {"label": _("Overdue"),         "value": overdue, "indicator": "red",    "datatype": "Int"},
        ]

    # ── Period helpers ────────────────────────────────────────────────────────

    def get_period(self, posting_date):
        if isinstance(posting_date, str):
            posting_date = getdate(posting_date)
        range_type = self.filters.get("range", "Monthly")
        if range_type == "Weekly":
            return _("Week {0} {1}").format(
                posting_date.isocalendar()[1], posting_date.year
            )
        elif range_type == "Quarterly":
            return _("Quarter {0} {1}").format(
                ((posting_date.month - 1) // 3) + 1, posting_date.year
            )
        elif range_type == "Yearly":
            return str(posting_date.year)
        else:  # Monthly (default)
            return self.months[posting_date.month - 1] + " " + str(posting_date.year)

    def get_period_date_ranges(self):
        from dateutil.relativedelta import MO, relativedelta

        from_date = getdate(self.filters.from_date)
        to_date   = getdate(self.filters.to_date)
        range_type = self.filters.get("range", "Monthly")

        increment = {"Monthly": 1, "Quarterly": 3, "Yearly": 12}.get(range_type, 1)

        if range_type in ["Monthly", "Quarterly"]:
            from_date = from_date.replace(day=1)
        elif range_type == "Yearly":
            from_date = from_date.replace(month=1, day=1)
        else:  # Weekly
            from_date = from_date + relativedelta(from_date, weekday=MO(-1))

        self.periodic_daterange = []
        for _dummy in range(1, 53):
            if range_type == "Weekly":
                period_end_date = add_days(from_date, 6)
            else:
                period_end_date = add_to_date(from_date, months=increment, days=-1)

            if period_end_date > to_date:
                period_end_date = to_date

            self.periodic_daterange.append(period_end_date)

            from_date = add_days(period_end_date, 1)
            if period_end_date == to_date:
                break
