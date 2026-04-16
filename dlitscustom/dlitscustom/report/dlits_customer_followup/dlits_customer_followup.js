// Copyright (c) 2026, DLITS and contributors
// For license information, please see license.txt

frappe.query_reports["Dlits Customer Followup"] = {

    filters: [
        {
            fieldname: "from_date",
            label:     __("From Date"),
            fieldtype: "Date",
            reqd:      1,
            default:   frappe.datetime.year_start(),
        },
        {
            fieldname: "to_date",
            label:     __("To Date"),
            fieldtype: "Date",
            reqd:      1,
            default:   frappe.datetime.get_today(),
        },
        {
            fieldname: "range",
            label:     __("Range"),
            fieldtype: "Select",
            options:   ["Weekly", "Monthly", "Quarterly", "Yearly"],
            default:   "Monthly",
            reqd:      1,
        },
        {
            fieldname: "group_by",
            label:     __("Group By"),
            fieldtype: "Select",
            options:   ["Owner", "Customer", "Status", "Priority"],
            default:   "Owner",
            reqd:      1,
        },
        {
            fieldname: "customer",
            label:     __("Customer"),
            fieldtype: "Link",
            options:   "Customer",
        },
        {
            fieldname: "task_owner",
            label:     __("Owner"),
            fieldtype: "Link",
            options:   "User",
        },
        {
            fieldname: "task_status",
            label:     __("Status"),
            fieldtype: "Select",
            options: [
                "",
                "Attempting Contact", "Contacted", "No Response", "Needs Follow-up",
                "Information Sent", "Meeting Scheduled", "Demo Scheduled",
                "Requirement Gathering", "Proposal Preparing", "Proposal Sent",
                "Negotiation", "Waiting Customer Decision",
                "On Hold", "Follow-up Later", "Future Opportunity",
                "Lost to Competitor", "No Budget", "Not Interested",
                "Wrong Contact", "Project Cancelled", "No Response (Closed)",
                "Completed", "Cancelled",
            ],
        },
        {
            fieldname: "priority",
            label:     __("Priority"),
            fieldtype: "Select",
            options:   ["", "Low", "Medium", "High", "Urgent"],
        },
        {
            fieldname: "is_payment_followup",
            label:     __("Payment Followups Only"),
            fieldtype: "Check",
        },
    ],

    // ── Row checkbox toggles the entity's chart line ──────────────────────────
    get_datatable_options(options) {
        return Object.assign(options, {
            checkboxColumn: true,
            events: {
                onCheckRow: function(data) {
                    if (!data || !frappe.query_report.chart) return;

                    const row_name   = data[2] && data[2].content;
                    if (!row_name) return;

                    const raw_data   = frappe.query_report.chart.data;
                    const new_datasets = raw_data.datasets.slice(); // shallow copy

                    const found_idx = new_datasets.findIndex(d => d.name === row_name);
                    if (found_idx !== -1) {
                        new_datasets.splice(found_idx, 1);          // deselect — remove line
                    } else {
                        // slice from col index 3 (entity + period columns; skip total)
                        new_datasets.push({
                            name:   row_name,
                            values: data.slice(3, data.length - 1)
                                        .map(col => parseFloat(col.content) || 0),
                        });
                    }

                    const new_data    = { labels: raw_data.labels, datasets: new_datasets };
                    const new_options = Object.assign({}, frappe.query_report.chart_options,
                                                      { data: new_data });
                    frappe.query_report.render_chart(new_options);
                    frappe.query_report.raw_chart_data = new_data;
                },
            },
        });
    },

    // ── Colour the Status column cells ────────────────────────────────────────
    formatter: function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname === "entity"
            && frappe.query_report.get_filter_value("group_by") === "Status") {
            const STATUS_COLORS = {
                "Attempting Contact":        "orange",
                "Contacted":                 "blue",
                "No Response":               "yellow",
                "Needs Follow-up":           "orange",
                "Information Sent":          "cyan",
                "Meeting Scheduled":         "blue",
                "Demo Scheduled":            "blue",
                "Requirement Gathering":     "purple",
                "Proposal Preparing":        "purple",
                "Proposal Sent":             "purple",
                "Negotiation":               "green",
                "Waiting Customer Decision": "yellow",
                "On Hold":                   "gray",
                "Follow-up Later":           "gray",
                "Future Opportunity":        "light-blue",
                "Lost to Competitor":        "red",
                "No Budget":                 "red",
                "Not Interested":            "red",
                "Wrong Contact":             "red",
                "Project Cancelled":         "red",
                "No Response (Closed)":      "red",
                "Completed":                 "green",
                "Cancelled":                 "gray",
            };
            const cls = STATUS_COLORS[data && data.entity] || "gray";
            return `<span class="indicator-pill ${cls} no-margin"
                        style="font-size:11px;font-weight:600;">${__(data.entity)}</span>`;
        }

        if (column.fieldname === "entity"
            && frappe.query_report.get_filter_value("group_by") === "Priority") {
            const PRIORITY_COLORS = {
                "Low": "gray", "Medium": "yellow", "High": "orange", "Urgent": "red"
            };
            const cls = PRIORITY_COLORS[data && data.entity] || "gray";
            return `<span class="indicator-pill ${cls} no-margin"
                        style="font-size:11px;font-weight:600;">${__(data.entity)}</span>`;
        }

        return value;
    },
};
