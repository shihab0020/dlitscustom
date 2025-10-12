frappe.ui.form.on('Sales Partner', {
    refresh: function(frm) {
        // Add custom buttons for commission management
        if (!frm.doc.__islocal) {
            add_commission_buttons(frm);
        }
    },
    
    after_save: function(frm) {
        // Refresh to show new buttons after save
        if (frm.doc.__islocal) {
            setTimeout(() => {
                frm.refresh();
            }, 1000);
        }
    }
});

function add_commission_buttons(frm) {
    // Add Commission Summary button
    frm.add_custom_button(__('Commission Summary'), function() {
        show_commission_summary(frm);
    }, __('Commission Management'));
    
    // Add Payment History button
    frm.add_custom_button(__('Payment History'), function() {
        show_payment_history(frm);
    }, __('Commission Management'));
    
    // Add Create Journal Entry button
    frm.add_custom_button(__('Create Journal Entry'), function() {
        create_commission_journal_entry(frm);
    }, __('Commission Management'));
    
    // Debug buttons (commented out for production)
    // frm.add_custom_button(__('Test Button'), function() {
    //     console.log('Test button clicked successfully!');
    //     frappe.msgprint('Test button is working!');
    // }, __('Commission Management'));
    
    // frm.add_custom_button(__('Test Account Lookup'), function() {
    //     test_account_lookup(frm);
    // }, __('Commission Management'));
    
    // frm.add_custom_button(__('Debug Commission Calculation'), function() {
    //     debug_commission_calculation(frm);
    // }, __('Commission Management'));
    
    // Add Create Payment button
    frm.add_custom_button(__('Create Payment'), function() {
        create_commission_payment(frm);
    }, __('Commission Management'));
    
    // Add View Linked Supplier button
    frm.add_custom_button(__('View Linked Supplier'), function() {
        view_linked_supplier(frm);
    }, __('Commission Management'));
    
    // Show linked supplier info
    show_linked_supplier_info(frm);
}

function show_commission_summary(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('Commission Summary for {0}', [frm.doc.partner_name]),
        fields: [
            {
                fieldtype: 'Date',
                fieldname: 'from_date',
                label: __('From Date'),
                default: frappe.datetime.add_months(frappe.datetime.get_today(), -3),
                reqd: 1
            },
            {
                fieldtype: 'Date',
                fieldname: 'to_date',
                label: __('To Date'),
                default: frappe.datetime.get_today(),
                reqd: 1
            },
            {
                fieldtype: 'Button',
                fieldname: 'get_summary',
                label: __('Get Summary')
            },
            {
                fieldtype: 'HTML',
                fieldname: 'summary_html'
            }
        ],
        primary_action_label: __('Close')
    });
    
    dialog.fields_dict.get_summary.input.onclick = function() {
        let from_date = dialog.get_value('from_date');
        let to_date = dialog.get_value('to_date');
        
        frappe.call({
            method: 'dlitscustom.utils.commission_management_dlits.get_sales_partner_commission_summary',
            args: {
                sales_partner: frm.doc.name,
                from_date: from_date,
                to_date: to_date
            },
            callback: function(r) {
                if (r.message) {
                    let data = r.message;
                    let html = `
                        <div class="commission-summary">
                            <div class="row">
                                <div class="col-md-6">
                                    <h5>Commission Overview</h5>
                                    <table class="table table-bordered">
                                        <tr><td><strong>Total Commission</strong></td><td>${format_currency(data.total_commission)}</td></tr>
                                        <tr><td><strong>Paid Commission</strong></td><td>${format_currency(data.paid_commission)}</td></tr>
                                        <tr class="text-danger"><td><strong>Outstanding Commission</strong></td><td>${format_currency(data.outstanding_commission)}</td></tr>
                                        <tr><td><strong>Commission Rate</strong></td><td>${data.commission_rate}%</td></tr>
                                    </table>
                                </div>
                                <div class="col-md-6">
                                    <h5>Sales Overview</h5>
                                    <table class="table table-bordered">
                                        <tr><td><strong>Total Orders</strong></td><td>${data.total_orders}</td></tr>
                                        <tr><td><strong>Total Sales</strong></td><td>${format_currency(data.total_sales)}</td></tr>
                                        <tr><td><strong>Linked Supplier</strong></td><td>${data.linked_supplier || 'Not Found'}</td></tr>
                                    </table>
                                </div>
                            </div>
                        </div>
                    `;
                    dialog.fields_dict.summary_html.$wrapper.html(html);
                }
            }
        });
    };
    
    dialog.show();
}

function show_payment_history(frm) {
    frappe.call({
        method: 'dlitscustom.utils.commission_management_dlits.get_sales_partner_payment_history',
        args: {
            sales_partner: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                let payments = r.message;
                
                if (payments.length === 0) {
                    frappe.msgprint(__('No payment history found for this Sales Partner.'));
                    return;
                }
                
                let dialog = new frappe.ui.Dialog({
                    title: __('Payment History for {0}', [frm.doc.partner_name]),
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'payment_history'
                        }
                    ],
                    size: 'large'
                });
                
                let html = '<table class="table table-bordered"><thead><tr><th>Date</th><th>Payment Entry</th><th>Amount</th><th>Mode</th><th>Reference</th><th>Remarks</th></tr></thead><tbody>';
                
                payments.forEach(payment => {
                    html += `<tr>
                        <td>${frappe.datetime.str_to_user(payment.reference_date)}</td>
                        <td><a href="/app/payment-entry/${payment.name}" target="_blank">${payment.name}</a></td>
                        <td>${format_currency(payment.paid_amount)}</td>
                        <td>${payment.mode_of_payment || ''}</td>
                        <td>${payment.reference_no || ''}</td>
                        <td>${payment.remarks || ''}</td>
                    </tr>`;
                });
                
                html += '</tbody></table>';
                dialog.fields_dict.payment_history.$wrapper.html(html);
                dialog.show();
            }
        }
    });
}

function create_commission_payment(frm) {
    // First get commission summary and linked supplier
    frappe.call({
        method: 'dlitscustom.utils.commission_management_dlits.get_sales_partner_commission_summary',
        args: {
            sales_partner: frm.doc.name,
            from_date: frappe.datetime.add_months(frappe.datetime.get_today(), -3),
            to_date: frappe.datetime.get_today()
        },
        callback: function(r) {
            if (r.message) {
                let data = r.message;
                
                if (!data.linked_supplier) {
                    frappe.msgprint(__('No linked supplier found for this Sales Partner. Please create a supplier first.'));
                    return;
                }
                
                if (data.outstanding_commission <= 0) {
                    frappe.msgprint(__('No outstanding commission found for this Sales Partner.'));
                    return;
                }
                
                // Debug: Show the data we're trying to set
                console.log('Commission Payment Data:', data);
                
                // Use frappe.route_options for reliable field setting
                frappe.route_options = {
                    'payment_type': 'Pay',
                    'party_type': 'Supplier',
                    'party': data.linked_supplier,
                    'paid_amount': data.outstanding_commission,
                    'received_amount': data.outstanding_commission,
                    'reference_date': frappe.datetime.get_today(),
                    'remarks': `Commission payment for Sales Partner: ${frm.doc.partner_name} (${frm.doc.name})`,
                    'mode_of_payment': 'Cash',
                    'reference_no': `SP-${frm.doc.name}-${frappe.datetime.get_today()}`,
                    'reference_date': frappe.datetime.get_today(),
                    'sales_partner': frm.doc.name  // Add sales partner for payment references
                };
                
                // Also store in window for backup
                window.sales_partner_payment_data = frappe.route_options;
                
                // Show confirmation message
                frappe.msgprint({
                    title: __('Creating Payment Entry'),
                    message: __('Opening Payment Entry with pre-filled data for supplier: {0}', [data.linked_supplier]),
                    indicator: 'blue'
                });
                
                // Navigate to new Payment Entry
                frappe.new_doc('Payment Entry');
            }
        }
    });
}

function view_linked_supplier(frm) {
    frappe.call({
        method: 'dlitscustom.override.sales_partner_dlits.get_sales_partner_supplier',
        args: {
            sales_partner: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                frappe.set_route('Form', 'Supplier', r.message);
            } else {
                frappe.msgprint(__('No linked supplier found for this Sales Partner.'));
            }
        }
    });
}

function create_commission_journal_entry(frm) {
    // console.log('Create Journal Entry clicked for:', frm.doc.name);
    
    // Show loading message
    frappe.show_alert({
        message: __('Loading commission data...'),
        indicator: 'blue'
    });
    
    // First get commission summary and linked supplier
    frappe.call({
        method: 'dlitscustom.utils.commission_management_dlits.get_sales_partner_commission_summary',
        args: {
            sales_partner: frm.doc.name,
            from_date: frappe.datetime.add_months(frappe.datetime.get_today(), -3),
            to_date: frappe.datetime.get_today()
        },
        callback: function(r) {
            // console.log('Commission summary response:', r);
            
            if (r.message) {
                let data = r.message;
                
                if (!data.linked_supplier) {
                    frappe.msgprint(__('No linked supplier found for this Sales Partner. Please create a supplier first.'));
                    return;
                }
                
                if (data.outstanding_commission <= 0) {
                    frappe.msgprint(__('No outstanding commission found for this Sales Partner.'));
                    return;
                }
                
                // Get commission details for Journal Entry
                frappe.call({
                    method: 'dlitscustom.utils.payment_references_dlits.get_commission_details_for_accrual',
                    args: {
                        sales_partner: frm.doc.name,
                        from_date: frappe.datetime.add_months(frappe.datetime.get_today(), -3),
                        to_date: frappe.datetime.get_today()
                    },
                    callback: function(r2) {
                        // console.log('Commission details response:', r2);
                        
                        if (r2.message && r2.message.length > 0) {
                            // Show dialog to select which commissions to accrue
                            show_commission_accrual_dialog(frm, data, r2.message);
                        } else {
                            frappe.msgprint(__('No commission transactions found to create Journal Entry.'));
                        }
                    },
                    error: function(r2) {
                        console.error('Error getting commission details:', r2);
                        frappe.msgprint(__('Error getting commission details. Please check console for details.'));
                    }
                });
            } else {
                frappe.msgprint(__('No commission data found.'));
            }
        },
        error: function(r) {
            console.error('Error getting commission summary:', r);
            frappe.msgprint(__('Error getting commission summary. Please check console for details.'));
        }
    });
}

function show_commission_accrual_dialog(frm, summary_data, commission_details) {
    console.log('Showing commission accrual dialog:', summary_data, commission_details);
    
    // Simplified approach - just show confirmation and create Journal Entry
    let total_amount = commission_details.reduce((sum, detail) => sum + detail.amount, 0);
    let transaction_list = commission_details.map(d => `${d.reference_doc} ${d.reference_name}: ${format_currency(d.amount)}`).join('<br>');
    
    frappe.confirm(
        `<div>
            <h5>Create Commission Journal Entry</h5>
            <p><strong>Sales Partner:</strong> ${frm.doc.partner_name}</p>
            <p><strong>Linked Supplier:</strong> ${summary_data.linked_supplier}</p>
            <p><strong>Total Commission:</strong> ${format_currency(total_amount)}</p>
            <hr>
            <p><strong>Commission Transactions:</strong></p>
            <div style="margin-left: 10px;">${transaction_list}</div>
            <hr>
            <p>This will create a Journal Entry with:</p>
            <ul>
                <li>Dr. Commission Expense: ${format_currency(total_amount)}</li>
                <li>Cr. Accounts Payable (${summary_data.linked_supplier}): ${format_currency(total_amount)}</li>
            </ul>
        </div>`,
        function() {
            // User confirmed, create Journal Entry
            create_journal_entry_form(frm, summary_data, commission_details, total_amount);
        },
        __('Create Commission Journal Entry')
    );
}

function create_journal_entry_form(frm, summary_data, selected_transactions, total_amount) {
    console.log('Creating Journal Entry form with data:', {
        summary_data: summary_data,
        selected_transactions: selected_transactions,
        total_amount: total_amount
    });
    
    // Show loading indicator
    frappe.show_alert({
        message: __('Creating Journal Entry...'),
        indicator: 'blue'
    });
    
    try {
        // Use frappe.route_options to pre-fill the Journal Entry
        frappe.route_options = {
            'voucher_type': 'Journal Entry',
            'posting_date': frappe.datetime.get_today(),
            'user_remark': `Commission accrual for Sales Partner: ${frm.doc.partner_name} (${frm.doc.name})`
        };
        
        // Store additional data for the Journal Entry form to use
        window.commission_journal_data = {
            sales_partner: frm.doc.name,
            sales_partner_name: frm.doc.partner_name,
            linked_supplier: summary_data.linked_supplier,
            total_amount: total_amount,
            transactions: selected_transactions
        };
        
        // Show success message
        frappe.show_alert({
            message: __('Journal Entry created successfully. Please add accounts and submit.'),
            indicator: 'green'
        });
        
        // Navigate to new Journal Entry
        frappe.new_doc('Journal Entry');
        
    } catch (error) {
        console.error('Error creating Journal Entry:', error);
        frappe.show_alert({
            message: __('Error creating Journal Entry: {0}', [error.message]),
            indicator: 'red'
        });
    }
}

function show_linked_supplier_info(frm) {
    frappe.call({
        method: 'dlitscustom.override.sales_partner_dlits.get_sales_partner_supplier',
        args: {
            sales_partner: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                frm.dashboard.add_indicator(__('Linked Supplier: {0}', [r.message]), 'green');
            } else {
                frm.dashboard.add_indicator(__('No Linked Supplier'), 'red');
            }
        }
    });
}

function test_account_lookup(frm) {
    console.log('Testing account lookup...');
    
    // First test the general test method
    frappe.call({
        method: 'dlitscustom.utils.payment_references_dlits.test_account_lookup',
        callback: function(r) {
            console.log('General test result:', r);
            
            if (r.message && r.message.success) {
                frappe.msgprint({
                    title: __('Account Lookup Test - General'),
                    message: `
                        <strong>Company:</strong> ${r.message.company}<br>
                        <strong>Test Supplier:</strong> ${r.message.supplier}<br>
                        <strong>Expense Account:</strong> ${r.message.accounts.expense_account || 'Not Found'}<br>
                        <strong>Payable Account:</strong> ${r.message.accounts.payable_account || 'Not Found'}<br>
                        ${r.message.accounts.error ? '<br><strong>Error:</strong> ' + r.message.accounts.error : ''}
                    `,
                    indicator: 'blue'
                });
            } else {
                frappe.msgprint({
                    title: __('Account Lookup Test Failed'),
                    message: r.message ? r.message.error : 'Unknown error',
                    indicator: 'red'
                });
            }
        },
        error: function(err) {
            console.error('Test failed:', err);
            frappe.msgprint({
                title: __('Test Error'),
                message: 'API call failed: ' + JSON.stringify(err),
                indicator: 'red'
            });
        }
    });
    
    // Test with current Sales Partner's linked supplier
    frappe.call({
        method: 'dlitscustom.override.sales_partner_dlits.get_sales_partner_supplier',
        args: {
            sales_partner: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                let company = frappe.defaults.get_default('company');
                console.log('Testing with Sales Partner supplier:', r.message);
                
                frappe.call({
                    method: 'dlitscustom.utils.payment_references_dlits.get_default_commission_accounts',
                    args: {
                        company: company,
                        supplier: r.message
                    },
                    callback: function(r2) {
                        console.log('Sales Partner specific test result:', r2);
                        
                        frappe.msgprint({
                            title: __('Account Lookup Test - Sales Partner Specific'),
                            message: `
                                <strong>Sales Partner:</strong> ${frm.doc.partner_name}<br>
                                <strong>Linked Supplier:</strong> ${r.message}<br>
                                <strong>Company:</strong> ${company}<br>
                                <strong>Expense Account:</strong> ${r2.message ? (r2.message.expense_account || 'Not Found') : 'Error'}<br>
                                <strong>Payable Account:</strong> ${r2.message ? (r2.message.payable_account || 'Not Found') : 'Error'}<br>
                                ${r2.message && r2.message.error ? '<br><strong>Error:</strong> ' + r2.message.error : ''}
                            `,
                            indicator: 'green'
                        });
                    },
                    error: function(err2) {
                        console.error('Sales Partner test failed:', err2);
                        frappe.msgprint({
                            title: __('Sales Partner Test Error'),
                            message: 'API call failed: ' + JSON.stringify(err2),
                            indicator: 'red'
                        });
                    }
                });
            } else {
                frappe.msgprint({
                    title: __('No Linked Supplier'),
                    message: 'This Sales Partner has no linked supplier to test with.',
                    indicator: 'orange'
                });
            }
        }
    });
}

function debug_commission_calculation(frm) {
    console.log('Debugging commission calculation...');
    
    frappe.call({
        method: 'dlitscustom.utils.commission_management_dlits.debug_commission_calculation',
        args: {
            sales_partner: frm.doc.name,
            from_date: frappe.datetime.add_months(frappe.datetime.get_today(), -3),
            to_date: frappe.datetime.get_today()
        },
        callback: function(r) {
            console.log('Commission debug result:', r);
            
            if (r.message) {
                let data = r.message;
                
                // Create detailed debug report
                let commission_sources = data.commission_sources;
                let payment_sources = data.payment_sources;
                let summary = data.summary;
                
                let html = `
                    <div class="commission-debug-report">
                        <h4>Commission Calculation Debug Report</h4>
                        <p><strong>Sales Partner:</strong> ${data.sales_partner}</p>
                        <p><strong>Linked Supplier:</strong> ${data.linked_supplier || 'Not Found'}</p>
                        <p><strong>Date Range:</strong> ${data.from_date} to ${data.to_date}</p>
                        
                        <hr>
                        <h5>Commission Sources</h5>
                        <table class="table table-bordered">
                            <tr><th>Source</th><th>Count</th><th>Commission</th><th>Sales</th></tr>
                            <tr>
                                <td>Sales Orders</td>
                                <td>${commission_sources.sales_orders.order_count || 0}</td>
                                <td>${format_currency(commission_sources.sales_orders.total_commission || 0)}</td>
                                <td>${format_currency(commission_sources.sales_orders.total_sales || 0)}</td>
                            </tr>
                            <tr>
                                <td>Sales Invoices</td>
                                <td>${commission_sources.sales_invoices.invoice_count || 0}</td>
                                <td>${format_currency(commission_sources.sales_invoices.total_commission || 0)}</td>
                                <td>${format_currency(commission_sources.sales_invoices.total_sales || 0)}</td>
                            </tr>
                        </table>
                        
                        <hr>
                        <h5>Payment Sources</h5>
                `;
                
                if (payment_sources) {
                    html += `
                        <h6>Direct Payments (${payment_sources.direct_payments.length})</h6>
                        <table class="table table-bordered">
                            <tr><th>Payment Entry</th><th>Date</th><th>Amount</th><th>Remarks</th></tr>
                    `;
                    
                    payment_sources.direct_payments.forEach(payment => {
                        html += `
                            <tr>
                                <td><a href="/app/payment-entry/${payment.name}" target="_blank">${payment.name}</a></td>
                                <td>${frappe.datetime.str_to_user(payment.reference_date)}</td>
                                <td>${format_currency(payment.paid_amount)}</td>
                                <td>${payment.remarks}</td>
                            </tr>
                        `;
                    });
                    
                    html += `</table>`;
                    
                    html += `
                        <h6>Journal Entry Payments (${payment_sources.journal_payments.length})</h6>
                        <table class="table table-bordered">
                            <tr><th>Payment Entry</th><th>Journal Entry</th><th>Date</th><th>Amount</th><th>Remarks</th></tr>
                    `;
                    
                    payment_sources.journal_payments.forEach(payment => {
                        html += `
                            <tr>
                                <td><a href="/app/payment-entry/${payment.payment_entry}" target="_blank">${payment.payment_entry}</a></td>
                                <td><a href="/app/journal-entry/${payment.journal_entry}" target="_blank">${payment.journal_entry}</a></td>
                                <td>${frappe.datetime.str_to_user(payment.reference_date)}</td>
                                <td>${format_currency(payment.allocated_amount)}</td>
                                <td>${payment.user_remark}</td>
                            </tr>
                        `;
                    });
                    
                    html += `</table>`;
                    
                    html += `
                        <h6>All Journal Entries (${payment_sources.all_journal_entries.length})</h6>
                        <table class="table table-bordered">
                            <tr><th>Journal Entry</th><th>Date</th><th>Total Amount</th><th>Allocated</th><th>Remarks</th></tr>
                    `;
                    
                    payment_sources.all_journal_entries.forEach(je => {
                        html += `
                            <tr>
                                <td><a href="/app/journal-entry/${je.name}" target="_blank">${je.name}</a></td>
                                <td>${frappe.datetime.str_to_user(je.posting_date)}</td>
                                <td>${format_currency(je.total_debit)}</td>
                                <td>${format_currency(je.allocated_amount)}</td>
                                <td>${je.user_remark}</td>
                            </tr>
                        `;
                    });
                    
                    html += `</table>`;
                }
                
                html += `
                        <hr>
                        <h5>Final Summary</h5>
                        <table class="table table-bordered">
                            <tr><td><strong>Total Commission</strong></td><td>${format_currency(summary.total_commission)}</td></tr>
                            <tr><td><strong>Paid Commission</strong></td><td>${format_currency(summary.paid_commission)}</td></tr>
                            <tr class="text-danger"><td><strong>Outstanding Commission</strong></td><td>${format_currency(summary.outstanding_commission)}</td></tr>
                        </table>
                    </div>
                `;
                
                frappe.msgprint({
                    title: __('Commission Calculation Debug'),
                    message: html,
                    wide: true
                });
                
            } else {
                frappe.msgprint({
                    title: __('Debug Failed'),
                    message: 'No debug data returned',
                    indicator: 'red'
                });
            }
        },
        error: function(err) {
            console.error('Debug failed:', err);
            frappe.msgprint({
                title: __('Debug Error'),
                message: 'API call failed: ' + JSON.stringify(err),
                indicator: 'red'
            });
        }
    });
}