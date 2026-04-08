frappe.query_reports["Dlits Customer Acquisition and Loyalty"] = {
    filters: [
        {
            fieldname: "view_type",
            label: __("View Type"),
            fieldtype: "Select",
            options: ["Monthly", "Territory Wise"],
            default: "Monthly",
            reqd: 1
        },
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company"),
            reqd: 1
        },
        {
            fieldname: "cost_center",
            label: __("Cost Center"),
            fieldtype: "Link",
            options: "Cost Center",
            // Dynamically filter cost centers based on the selected company
            get_query: () => {
                const company = frappe.query_report.get_filter_value('company');
                return {
                    filters: { 'company': company }
                };
            }
        },
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -12),
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },
    ],

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if ((column.fieldname === "new_customers" || column.fieldname === "repeat_customers") && data && data[column.fieldname] > 0) {
            const list_field = column.fieldname + "_list";
            const customer_names = data[list_field];
            
            if (customer_names) {
                return `<div class="customer-drilldown-trigger" 
                             data-names="${customer_names}" 
                             data-label="${column.label}" 
                             data-period="${data.month}"
                             style="color: #2196F3; font-weight: bold; cursor: pointer; text-decoration: underline;">
                             ${value}
                        </div>`;
            }
        }
        return value;
    },

    onload: function (report) {
        const self = this;
        
        // Clean up previous listeners to prevent memory leaks or double-firing
        $(report.page.main).off("click", ".customer-drilldown-trigger");
        $(document).off("click", ".route-link");

        // Listener for the grid links
        $(report.page.main).on("click", ".customer-drilldown-trigger", function (e) {
            e.preventDefault();
            const names_str = $(this).attr("data-names");
            const label = $(this).attr("data-label");
            const period = $(this).attr("data-period");
            if (names_str) {
                const names = names_str.split("||");
                self.show_drilldown(names, label, period);
            }
        });

        // Listener for customer links inside the popup dialog
        $(document).on("click", ".route-link", function(e) {
            e.preventDefault();
            frappe.set_route("Form", $(this).data("doctype"), $(this).data("name"));
        });
    },

    show_drilldown: function (names, label, period) {
        let rows = names.map((name, i) => `
            <tr>
                <td>${i + 1}</td>
                <td>
                    <span class="route-link" 
                          data-doctype="Customer" 
                          data-name="${name}" 
                          style="color: var(--blue-500); cursor: pointer; font-weight: 500;">
                        ${name}
                    </span>
                </td>
            </tr>
        `).join("");

        let html = `
            <div style="padding: 10px; max-height: 400px; overflow-y: auto;">
                <table class="table table-bordered table-condensed">
                    <thead>
                        <tr class="active">
                            <th style="width: 40px">#</th>
                            <th>${__("Customer Name")}</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>`;

        frappe.msgprint({
            title: __("{0} Customers - {1}", [label, period]),
            message: html,
            wide: true
        });
    }
};