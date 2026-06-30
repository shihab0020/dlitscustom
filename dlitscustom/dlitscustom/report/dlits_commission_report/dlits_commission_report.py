import frappe
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"fieldname": "name",              "label": "Commission Doc",  "fieldtype": "Link",     "options": "Dlits Commission Management", "width": 180},
        {"fieldname": "sales_partner",     "label": "Partner",         "fieldtype": "Link",     "options": "Dlits Sales Partner",         "width": 150},
        {"fieldname": "partner_name",      "label": "Partner Name",    "fieldtype": "Data",     "width": 160},
        {"fieldname": "from_date",         "label": "From",            "fieldtype": "Date",     "width": 100},
        {"fieldname": "to_date",           "label": "To",              "fieldtype": "Date",     "width": 100},
        {"fieldname": "invoice_count",     "label": "Invoices",        "fieldtype": "Int",      "width": 80},
        {"fieldname": "total_net_amount",  "label": "Net Total",       "fieldtype": "Currency", "width": 130},
        {"fieldname": "total_commission",  "label": "Commission",      "fieldtype": "Currency", "width": 130},
        {"fieldname": "total_paid",        "label": "Paid",            "fieldtype": "Currency", "width": 120},
        {"fieldname": "balance_commission","label": "Balance",         "fieldtype": "Currency", "width": 120},
        {"fieldname": "status",            "label": "Status",          "fieldtype": "Data",     "width": 140},
        {"fieldname": "approved_by",       "label": "Approved By",     "fieldtype": "Link",     "options": "User", "width": 150},
        {"fieldname": "approved_on",       "label": "Approved On",     "fieldtype": "Date",     "width": 100},
        {"fieldname": "commission_rate",   "label": "Rate (%)",        "fieldtype": "Percent",  "width": 80},
    ]


def get_data(filters):
    conditions = "WHERE dcm.docstatus != 2"
    values = {}

    if filters.get("from_date"):
        conditions += " AND dcm.from_date >= %(from_date)s"
        values["from_date"] = filters["from_date"]
    if filters.get("to_date"):
        conditions += " AND dcm.to_date <= %(to_date)s"
        values["to_date"] = filters["to_date"]
    if filters.get("sales_partner"):
        conditions += " AND dcm.sales_partner = %(sales_partner)s"
        values["sales_partner"] = filters["sales_partner"]
    if filters.get("status"):
        conditions += " AND dcm.status = %(status)s"
        values["status"] = filters["status"]

    rows = frappe.db.sql(f"""
        SELECT
            dcm.name,
            dcm.sales_partner,
            dsp.partner_name,
            dcm.from_date,
            dcm.to_date,
            COUNT(dci.name)       AS invoice_count,
            dcm.total_net_amount,
            dcm.total_commission,
            dcm.total_paid,
            dcm.balance_commission,
            dcm.status,
            dcm.commission_rate,
            dcm.approved_by,
            dcm.approved_on
        FROM `tabDlits Commission Management` dcm
        LEFT JOIN `tabDlits Sales Partner` dsp ON dsp.name = dcm.sales_partner
        LEFT JOIN `tabDlits Commission Invoice` dci ON dci.parent = dcm.name
        {conditions}
        GROUP BY dcm.name
        ORDER BY dcm.from_date DESC, dcm.sales_partner
    """, values, as_dict=True)

    # Colour-code status for readability
    status_colour = {
        "Draft":                   "",
        "Calculated":              "blue",
        "Requested for Approval":  "orange",
        "Approved":                "green",
        "Paid":                    "darkgreen",
    }

    result = []
    for row in rows:
        colour = status_colour.get(row.status or "", "")
        if colour:
            row["status"] = f"""<span style="color:{colour};font-weight:600">{row.status}</span>"""
        result.append(row)

    return result
