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
            "fieldname": "transaction_type",
            "label": __("Transaction Type"),
            "fieldtype": "Select",
            "options": "\nSales\nPurchase",
            "default": ""
        },
        {
            "fieldname": "tax_account",
            "label": __("Tax Account"),
            "fieldtype": "Link",
            "options": "Account",
            "get_query": function() {
                return {
                    "filters": {
                        "account_type": ["in", ["Tax", "Chargeable"]],
                        "is_group": 0
                    }
                };
            }
        },
        {
            "fieldname": "tax_rate",
            "label": __("Tax Rate (%)"),
            "fieldtype": "Float",
            "precision": 2
        },
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        },
        {
            "fieldname": "supplier",
            "label": __("Supplier"),
            "fieldtype": "Link",
            "options": "Supplier"
        }
    ],
    
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        // Format summary rows
        if (data && data.tax_account) {
            if (data.tax_account.includes('<b>') || data.tax_account.includes('Total')) {
                value = `<div style="font-weight: bold; color: #2e7d32;">${value}</div>`;
            }
            
            if (data.tax_account.includes('─')) {
                return `<div style="border-top: 2px solid #ddd; margin: 5px 0;"></div>`;
            }
        }
        
        // Color code transaction types
        if (column.fieldname === "transaction_type" && data) {
            if (data.transaction_type === "Sales") {
                value = `<span style="color: #28a745; font-weight: bold;">${value}</span>`;
            } else if (data.transaction_type === "Purchase") {
                value = `<span style="color: #dc3545; font-weight: bold;">${value}</span>`;
            }
        }
        
        // Format tax amounts
        if (column.fieldname === "tax_amount" && data && data.tax_amount) {
            if (data.transaction_type === "Sales") {
                value = `<span style="color: #28a745;">${value}</span>`;
            } else if (data.transaction_type === "Purchase") {
                value = `<span style="color: #dc3545;">${value}</span>`;
            }
        }
        
        return value;
    },
    
    "onload": function(report) {
        // Add custom buttons for export functionality
        report.page.add_inner_button(__("Export to PDF"), function() {
            let filters = report.get_values();
            let filter_string = get_filter_string(filters);
            
            frappe.call({
                method: "frappe.utils.print_format.download_pdf",
                args: {
                    doctype: "Sales Taxes and Charges",
                    name: "DLITS Tax Report",
                    format: "Standard",
                    doc: {
                        "name": "DLITS Tax Report",
                        "filters": filters,
                        "data": report.data || []
                    }
                },
                callback: function(r) {
                    if (r.message) {
                        // Create a more comprehensive PDF export
                        export_to_pdf(report, filters);
                    }
                }
            });
        }, __("Export"));
        
        report.page.add_inner_button(__("Export to Excel"), function() {
            let filters = report.get_values();
            export_to_excel(report, filters);
        }, __("Export"));
        
        // Add refresh button
        report.page.add_inner_button(__("Refresh"), function() {
            report.refresh();
        }, __("Actions"));
    }
};

function get_filter_string(filters) {
    let filter_parts = [];
    
    if (filters.from_date) filter_parts.push(`From: ${filters.from_date}`);
    if (filters.to_date) filter_parts.push(`To: ${filters.to_date}`);
    if (filters.transaction_type) filter_parts.push(`Type: ${filters.transaction_type}`);
    if (filters.tax_account) filter_parts.push(`Tax Account: ${filters.tax_account}`);
    if (filters.tax_rate) filter_parts.push(`Tax Rate: ${filters.tax_rate}%`);
    if (filters.customer) filter_parts.push(`Customer: ${filters.customer}`);
    if (filters.supplier) filter_parts.push(`Supplier: ${filters.supplier}`);
    
    return filter_parts.join(" | ");
}

function export_to_pdf(report, filters) {
    let data = report.data || [];
    let columns = report.columns || [];
    
    // Create HTML content for PDF
    let html_content = `
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #2e7d32; margin-bottom: 10px;">DLITS Tax Report</h1>
            <p style="color: #666; font-size: 14px;">${get_filter_string(filters)}</p>
            <p style="color: #666; font-size: 12px;">Generated on: ${frappe.datetime.now_datetime()}</p>
        </div>
        
        <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
            <thead>
                <tr style="background-color: #f8f9fa;">
                    ${columns.map(col => `<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">${col.label}</th>`).join('')}
                </tr>
            </thead>
            <tbody>
                ${data.map(row => `
                    <tr>
                        ${columns.map(col => {
                            let value = row[col.fieldname] || '';
                            if (col.fieldtype === 'Currency') {
                                value = format_currency(value);
                            }
                            return `<td style="border: 1px solid #ddd; padding: 6px;">${value}</td>`;
                        }).join('')}
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    // Create and download PDF
    let pdf_window = window.open('', '_blank');
    pdf_window.document.write(`
        <html>
            <head>
                <title>DLITS Tax Report</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    table { page-break-inside: auto; }
                    tr { page-break-inside: avoid; page-break-after: auto; }
                </style>
            </head>
            <body>
                ${html_content}
                <script>
                    window.onload = function() {
                        window.print();
                        setTimeout(function() { window.close(); }, 1000);
                    };
                </script>
            </body>
        </html>
    `);
    pdf_window.document.close();
}

function export_to_excel(report, filters) {
    let data = report.data || [];
    let columns = report.columns || [];
    
    if (!data.length) {
        frappe.msgprint(__("No data to export"));
        return;
    }
    
    // Prepare data for Excel export
    let excel_data = [];
    
    // Add header with report title and filters
    excel_data.push(['DLITS Tax Report']);
    excel_data.push([get_filter_string(filters)]);
    excel_data.push([`Generated on: ${frappe.datetime.now_datetime()}`]);
    excel_data.push([]); // Empty row
    
    // Add column headers
    excel_data.push(columns.map(col => col.label));
    
    // Add data rows
    data.forEach(row => {
        let excel_row = columns.map(col => {
            let value = row[col.fieldname] || '';
            if (col.fieldtype === 'Currency' && value) {
                return parseFloat(value) || 0;
            }
            return value;
        });
        excel_data.push(excel_row);
    });
    
    // Create and download Excel file
    let worksheet = XLSX.utils.aoa_to_sheet(excel_data);
    let workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Tax Report");
    
    // Set column widths
    let col_widths = columns.map(col => ({wch: Math.max(col.label.length, 15)}));
    worksheet['!cols'] = col_widths;
    
    // Generate filename with timestamp
    let filename = `DLITS_Tax_Report_${frappe.datetime.now_date()}.xlsx`;
    
    // Download file
    XLSX.writeFile(workbook, filename);
    
    frappe.show_alert({
        message: __("Excel file downloaded successfully"),
        indicator: "green"
    });
}

function format_currency(value) {
    if (!value) return '0.00';
    return parseFloat(value).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Load XLSX library if not already loaded
if (typeof XLSX === 'undefined') {
    frappe.require('/assets/frappe/js/lib/xlsx.full.min.js');
}