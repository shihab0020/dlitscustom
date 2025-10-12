// Copyright (c) 2024, DLITS and contributors
// For license information, please see license.txt

frappe.query_reports["DLITS Tax Report"] = {
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
            "fieldname": "tax_type",
            "label": __("Tax Type"),
            "fieldtype": "Data"
        }
    ],
    
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname == "net_tax_amount" && data) {
            if (flt(data.net_tax_amount) > 0) {
                value = "<span style='color:green; font-weight:bold'>" + value + "</span>";
            } else if (flt(data.net_tax_amount) < 0) {
                value = "<span style='color:red; font-weight:bold'>" + value + "</span>";
            }
        }
        
        if (column.fieldname == "sales_tax_amount" && data && flt(data.sales_tax_amount) > 0) {
            value = "<span style='color:green'>" + value + "</span>";
        }
        
        if (column.fieldname == "purchase_tax_amount" && data && flt(data.purchase_tax_amount) > 0) {
            value = "<span style='color:blue'>" + value + "</span>";
        }
        
        return value;
    },
    
    "onload": function(report) {
        // Add PDF Export button
        report.page.add_inner_button(__("Export PDF"), function() {
            let filters = report.get_values();
            let data = report.data || [];
            generate_pdf_report(data, filters, "DLITS Tax Report");
        });
        
        // Add Print button
        report.page.add_inner_button(__("Print"), function() {
            let filters = report.get_values();
            let data = report.data || [];
            generate_pdf_report(data, filters, "DLITS Tax Report");
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
    if (filters.tax_type) {
        filter_array.push("Tax Type: " + filters.tax_type);
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
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Tax Type</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">Rate (%)</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Sales Tax</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Purchase Tax</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Net Tax</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Sales Base</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Purchase Base</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">Sales Inv.</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">Purchase Inv.</th>
                </tr>
            </thead>
            <tbody>`;
    
    let total_sales_tax = 0, total_purchase_tax = 0, total_net_tax = 0;
    let total_sales_base = 0, total_purchase_base = 0;
    let total_sales_invoices = 0, total_purchase_invoices = 0;
    
    data.forEach(function(row) {
        total_sales_tax += flt(row.sales_tax_amount);
        total_purchase_tax += flt(row.purchase_tax_amount);
        total_net_tax += flt(row.net_tax_amount);
        total_sales_base += flt(row.sales_base_amount);
        total_purchase_base += flt(row.purchase_base_amount);
        total_sales_invoices += flt(row.sales_invoices_count);
        total_purchase_invoices += flt(row.purchase_invoices_count);
        
        let net_tax_color = '';
        if (flt(row.net_tax_amount) > 0) {
            net_tax_color = 'color: green; font-weight: bold;';
        } else if (flt(row.net_tax_amount) < 0) {
            net_tax_color = 'color: red; font-weight: bold;';
        }
        
        html_content += `
            <tr>
                <td style="border: 1px solid #ddd; padding: 6px;">${row.tax_type}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: center;">${flt(row.tax_rate).toFixed(1)}%</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right; color: green;">${format_currency(row.sales_tax_amount)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right; color: blue;">${format_currency(row.purchase_tax_amount)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right; ${net_tax_color}">${format_currency(row.net_tax_amount)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">${format_currency(row.sales_base_amount)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">${format_currency(row.purchase_base_amount)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: center;">${flt(row.sales_invoices_count)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: center;">${flt(row.purchase_invoices_count)}</td>
            </tr>`;
    });
    
    // Add totals row
    let total_net_color = '';
    if (total_net_tax > 0) {
        total_net_color = 'color: green; font-weight: bold;';
    } else if (total_net_tax < 0) {
        total_net_color = 'color: red; font-weight: bold;';
    }
    
    html_content += `
            <tr style="background-color: #f8f9fa; font-weight: bold;">
                <td style="border: 1px solid #ddd; padding: 6px;" colspan="2">TOTAL</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right; color: green;">${format_currency(total_sales_tax)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right; color: blue;">${format_currency(total_purchase_tax)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right; ${total_net_color}">${format_currency(total_net_tax)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">${format_currency(total_sales_base)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">${format_currency(total_purchase_base)}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: center;">${total_sales_invoices}</td>
                <td style="border: 1px solid #ddd; padding: 6px; text-align: center;">${total_purchase_invoices}</td>
            </tr>
        </tbody>
    </table>
    
    <div style="margin-top: 30px; font-size: 11px; color: #666;">
        <p><strong>Tax Summary:</strong></p>
        <ul>
            <li>Total Tax Types: ${data.length}</li>
            <li>Net Tax Position: ${format_currency(total_net_tax)} ${total_net_tax > 0 ? '(Tax Payable)' : total_net_tax < 0 ? '(Tax Refundable)' : '(Balanced)'}</li>
            <li>Total Sales Tax Collected: ${format_currency(total_sales_tax)}</li>
            <li>Total Purchase Tax Paid: ${format_currency(total_purchase_tax)}</li>
        </ul>
        <p><strong>Legend:</strong></p>
        <ul>
            <li><span style="color: green;">Green</span> = Sales Tax (Tax Collected)</li>
            <li><span style="color: blue;">Blue</span> = Purchase Tax (Tax Paid)</li>
            <li><span style="color: green; font-weight: bold;">Bold Green</span> = Net Tax Payable</li>
            <li><span style="color: red; font-weight: bold;">Bold Red</span> = Net Tax Refundable</li>
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

function format_currency(value) {
    return frappe.format(flt(value), {fieldtype: 'Currency'});
}