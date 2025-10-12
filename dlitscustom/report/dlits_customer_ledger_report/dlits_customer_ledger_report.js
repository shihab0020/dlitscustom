// Copyright (c) 2024, DLITS and contributors
// For license information, please see license.txt

frappe.query_reports["DLITS Customer Ledger Report"] = {
    "filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        }
    ],
    
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname == "outstanding_amount" && data && flt(data.outstanding_amount) > 0) {
            value = "<span style='color:red'>" + value + "</span>";
        }
        
        if (column.fieldname == "aging_over_90" && data && flt(data.aging_over_90) > 0) {
            value = "<span style='color:red; font-weight:bold'>" + value + "</span>";
        }
        
        return value;
    },
    
    "onload": function(report) {
        // Add PDF Export button
        report.page.add_inner_button(__("Export PDF"), function() {
            let filters = report.get_values();
            let filter_string = get_filter_string(filters);
            
            frappe.call({
                method: "dlitscustom.dlitscustom.report.dlits_customer_ledger_report.dlits_customer_ledger_report.get_pdf_data",
                args: {
                    filters: filters
                },
                callback: function(r) {
                    if (r.message) {
                        generate_pdf_report(r.message, filters, "DLITS Customer Ledger Report");
                    }
                }
            });
        });
        
        // Add Print button
        report.page.add_inner_button(__("Print"), function() {
            let filters = report.get_values();
            print_report(report, filters, "DLITS Customer Ledger Report");
        });
    }
};

function get_filter_string(filters) {
    let filter_array = [];
    
    if (filters.from_date) {
        filter_array.push("From: " + frappe.datetime.str_to_user(filters.from_date));
    }
    if (filters.to_date) {
        filter_array.push("To: " + frappe.datetime.str_to_user(filters.to_date));
    }
    if (filters.customer) {
        filter_array.push("Customer: " + filters.customer);
    }
    
    return filter_array.join(" | ");
}

function generate_pdf_report(data, filters, report_name) {
    let filter_string = get_filter_string(filters);
    
    let html_content = `
        <div style="text-align: center; margin-bottom: 30px;">
            <h2 style="margin: 0; color: #333;">${report_name}</h2>
            <p style="margin: 5px 0; color: #666;">${filter_string}</p>
            <p style="margin: 5px 0; color: #666;">Generated on: ${frappe.datetime.str_to_user(frappe.datetime.get_today())}</p>
        </div>
        
        <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
            <thead>
                <tr style="background-color: #f8f9fa;">
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Customer</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Total Invoiced</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Total Paid</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Outstanding</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">0-30 Days</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">31-60 Days</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">61-90 Days</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Over 90 Days</th>
                </tr>
            </thead>
            <tbody>`;
    
    let total_invoiced = 0, total_paid = 0, total_outstanding = 0;
    let total_0_30 = 0, total_31_60 = 0, total_61_90 = 0, total_over_90 = 0;
    
    data.forEach(function(row) {
        total_invoiced += flt(row.total_invoiced);
        total_paid += flt(row.total_paid);
        total_outstanding += flt(row.outstanding_amount);
        total_0_30 += flt(row.aging_0_30);
        total_31_60 += flt(row.aging_31_60);
        total_61_90 += flt(row.aging_61_90);
        total_over_90 += flt(row.aging_over_90);
        
        html_content += `
            <tr>
                <td style="border: 1px solid #ddd; padding: 6px;">${row.customer_name || row.customer}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">${format_currency(row.total_invoiced)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">${format_currency(row.total_paid)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right; ${flt(row.outstanding_amount) > 0 ? 'color: red; font-weight: bold;' : ''}">${format_currency(row.outstanding_amount)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">${format_currency(row.aging_0_30)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">${format_currency(row.aging_31_60)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">${format_currency(row.aging_61_90)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right; ${flt(row.aging_over_90) > 0 ? 'color: red; font-weight: bold;' : ''}">${format_currency(row.aging_over_90)}</td>
            </tr>`;
    });
    
    // Add totals row
    html_content += `
            <tr style="background-color: #f8f9fa; font-weight: bold;">
                <td style="border: 1px solid #ddd; padding: 6px;">TOTAL</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">${format_currency(total_invoiced)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">${format_currency(total_paid)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right; color: red;">${format_currency(total_outstanding)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">${format_currency(total_0_30)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">${format_currency(total_31_60)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">${format_currency(total_61_90)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right; color: red;">${format_currency(total_over_90)}</td>
            </tr>
        </tbody>
    </table>
    
    <div style="margin-top: 30px; font-size: 11px; color: #666;">
        <p><strong>Summary:</strong></p>
        <ul>
            <li>Total Customers: ${data.length}</li>
            <li>Total Outstanding: ${format_currency(total_outstanding)}</li>
            <li>Overdue (>90 days): ${format_currency(total_over_90)}</li>
        </ul>
    </div>`;
    
    // Create and download PDF
    let pdf_window = window.open('', '_blank');
    pdf_window.document.write(`
        <html>
            <head>
                <title>${report_name}</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    @media print { body { margin: 0; } }
                </style>
            </head>
            <body>
                ${html_content}
                <script>
                    window.onload = function() {
                        window.print();
                    }
                </script>
            </body>
        </html>
    `);
    pdf_window.document.close();
}

function print_report(report, filters, report_name) {
    let data = report.data || [];
    generate_pdf_report(data, filters, report_name);
}

function format_currency(value) {
    return frappe.format(flt(value), {fieldtype: 'Currency'});
}