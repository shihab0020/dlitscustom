// Copyright (c) 2024, DLITS and contributors
// For license information, please see license.txt

frappe.ui.form.on('DLITS Sales Partner', {
    refresh: function(frm) {
        // Add custom buttons
        add_custom_buttons(frm);
        
        // Set field properties
        set_field_properties(frm);
        
        // Update commission totals if saved
        if (!frm.is_new()) {
            update_commission_display(frm);
        }
    },
    
    commission_type: function(frm) {
        // Update commission rate label based on type
        update_commission_rate_label(frm);
        
        // Clear commission rate when type changes
        if (frm.doc.commission_rate) {
            frm.set_value('commission_rate', 0);
        }
    },
    
    commission_rate: function(frm) {
        // Validate commission rate based on type
        validate_commission_rate(frm);
    },
    
    auto_create_supplier: function(frm) {
        // Show/hide supplier field based on auto create setting
        if (frm.doc.auto_create_supplier) {
            frm.set_df_property('supplier', 'read_only', 1);
            frm.set_df_property('supplier', 'description', 'Supplier will be created automatically');
        } else {
            frm.set_df_property('supplier', 'read_only', 0);
            frm.set_df_property('supplier', 'description', 'Select existing supplier or leave blank');
        }
    },
    
    partner_name: function(frm) {
        // Generate partner code if not set
        if (frm.doc.partner_name && !frm.doc.partner_code) {
            generate_partner_code(frm);
        }
    },
    
    start_date: function(frm) {
        // Validate start date
        if (frm.doc.start_date && frm.doc.end_date) {
            if (frm.doc.start_date >= frm.doc.end_date) {
                frappe.msgprint(__('Start date must be before end date'));
                frm.set_value('start_date', '');
            }
        }
    },
    
    end_date: function(frm) {
        // Validate end date
        if (frm.doc.start_date && frm.doc.end_date) {
            if (frm.doc.end_date <= frm.doc.start_date) {
                frappe.msgprint(__('End date must be after start date'));
                frm.set_value('end_date', '');
            }
        }
    }
});

function add_custom_buttons(frm) {
    if (!frm.is_new()) {
        // Update Totals button
        frm.add_custom_button(__('Update Commission Totals'), function() {
            update_commission_totals(frm);
        }, __('Actions'));
        
        // Payment buttons
        if (frm.doc.outstanding_commission > 0) {
            // Quick Pay Full Amount button
            frm.add_custom_button(__('Pay Full Outstanding'), function() {
                create_quick_payment(frm, frm.doc.outstanding_commission);
            }, __('Payments'));
            
            // Custom Payment Amount button
            frm.add_custom_button(__('Custom Payment'), function() {
                create_commission_payment(frm);
            }, __('Payments'));
            
            // Partial Payment button
            frm.add_custom_button(__('Partial Payment'), function() {
                create_partial_payment(frm);
            }, __('Payments'));
            
            // Journal Entry for Accrual
            frm.add_custom_button(__('Create Journal Entry'), function() {
                create_commission_journal_entry(frm);
            }, __('Payments'));
        }
        
        // Create/Link Supplier button
        if (!frm.doc.supplier) {
            frm.add_custom_button(__('Create Supplier'), function() {
                create_supplier_for_partner(frm);
            }, __('Actions'));
        }
        
        // View Commission Report button
        frm.add_custom_button(__('View Commission Report'), function() {
            view_commission_report(frm);
        }, __('Reports'));
        
        // View Sales Invoices button
        frm.add_custom_button(__('View Sales Invoices'), function() {
            view_sales_invoices(frm);
        }, __('Reports'));
        
        // Commission Summary button
        frm.add_custom_button(__('Commission Summary'), function() {
            show_commission_summary(frm);
        }, __('Reports'));
        
        // Payment History button
        if (frm.doc.supplier) {
            frm.add_custom_button(__('Payment History'), function() {
                view_payment_history(frm);
            }, __('Reports'));
        }
        
        // Fix Commission Status button (one-time fix for existing payments)
        frm.add_custom_button(__('Fix Commission Status'), function() {
            fix_existing_commission_payments(frm);
        }, __('Actions'));
    }
}

function set_field_properties(frm) {
    // Set commission rate label based on type
    update_commission_rate_label(frm);
    
    // Set auto create supplier behavior
    if (frm.doc.auto_create_supplier) {
        frm.set_df_property('supplier', 'read_only', 1);
        frm.set_df_property('supplier', 'description', 'Supplier will be created automatically');
    }
    
    // Set tracking fields as read-only
    frm.set_df_property('total_sales', 'read_only', 1);
    frm.set_df_property('total_commission_earned', 'read_only', 1);
    frm.set_df_property('total_commission_paid', 'read_only', 1);
    frm.set_df_property('outstanding_commission', 'read_only', 1);
    frm.set_df_property('last_commission_date', 'read_only', 1);
}

function update_commission_rate_label(frm) {
    if (frm.doc.commission_type === 'Percentage') {
        frm.set_df_property('commission_rate', 'label', 'Commission Rate (%)');
        frm.set_df_property('commission_rate', 'description', 'Enter percentage (e.g., 5 for 5%)');
    } else {
        frm.set_df_property('commission_rate', 'label', 'Commission Amount');
        frm.set_df_property('commission_rate', 'description', 'Enter fixed amount per transaction');
    }
}

function validate_commission_rate(frm) {
    if (frm.doc.commission_type === 'Percentage') {
        if (frm.doc.commission_rate > 100) {
            frappe.msgprint(__('Commission percentage cannot exceed 100%'));
            frm.set_value('commission_rate', 0);
        }
    }
    
    if (frm.doc.commission_rate < 0) {
        frappe.msgprint(__('Commission rate cannot be negative'));
        frm.set_value('commission_rate', 0);
    }
}

function generate_partner_code(frm) {
    // Generate partner code based on partner name
    let name = frm.doc.partner_name;
    let code = name.replace(/[^a-zA-Z]/g, '').substring(0, 3).toUpperCase();
    
    if (code.length < 3) {
        code = code.padEnd(3, 'X');
    }
    
    // Add random number for uniqueness
    code += Math.floor(Math.random() * 9999).toString().padStart(4, '0');
    
    frm.set_value('partner_code', code);
}

function update_commission_totals(frm) {
    frappe.call({
        method: 'dlitscustom.dlitscustom.doctype.dlits_sales_partner.dlits_sales_partner.update_partner_totals',
        args: {
            sales_partner: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                frm.set_value('total_sales', r.message.total_sales);
                frm.set_value('total_commission_earned', r.message.total_commission_earned);
                frm.set_value('total_commission_paid', r.message.total_commission_paid);
                frm.set_value('outstanding_commission', r.message.outstanding_commission);
                
                frappe.msgprint(__('Commission totals updated successfully'));
                frm.refresh();
            }
        }
    });
}

function create_commission_payment(frm) {
    let outstanding = frm.doc.outstanding_commission;
    
    frappe.prompt([
        {
            label: 'Payment Amount',
            fieldname: 'amount',
            fieldtype: 'Currency',
            default: outstanding,
            reqd: 1
        },
        {
            label: 'Pay From Account',
            fieldname: 'paid_from_account',
            fieldtype: 'Link',
            options: 'Account',
            get_query: function() {
                return {
                    filters: {
                        'account_type': ['in', ['Cash', 'Bank']],
                        'is_group': 0,
                        'company': frappe.defaults.get_user_default('Company')
                    }
                };
            },
            description: 'Select the account to pay from (Cash/Bank account)'
        },
        {
            label: 'Reference',
            fieldname: 'reference',
            fieldtype: 'Data',
            description: 'Optional reference for this payment'
        }
    ], function(values) {
        frappe.call({
            method: 'dlitscustom.dlitscustom.doctype.dlits_sales_partner.dlits_sales_partner.create_commission_payment',
            args: {
                sales_partner: frm.doc.name,
                amount: values.amount,
                reference_doc: values.reference,
                paid_from_account: values.paid_from_account
            },
            callback: function(r) {
                if (r.message && r.message.payment_entry) {
                    frappe.msgprint(__('Payment entry created successfully'));
                    
                    // Ask if user wants to open the payment entry
                    frappe.confirm(__('Do you want to open the payment entry?'), function() {
                        frappe.set_route('Form', 'Payment Entry', r.message.payment_entry.name);
                    });
                    
                    // Update totals
                    update_commission_totals(frm);
                }
            }
        });
    }, __('Create Commission Payment'), __('Create'));
}

function view_commission_report(frm) {
    // Use direct URL to avoid getdoctype issues
    let url = `/app/query-report/DLITS%20Sales%20Partner%20Commission%20Report?sales_partner=${encodeURIComponent(frm.doc.name)}`;
    window.open(url, '_blank');
}

function view_sales_invoices(frm) {
    frappe.set_route('List', 'Sales Invoice', {
        'dlits_sales_partner': frm.doc.name
    });
}

function show_commission_summary(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('Commission Summary'),
        fields: [
            {
                label: 'From Date',
                fieldname: 'from_date',
                fieldtype: 'Date',
                default: frappe.datetime.add_months(frappe.datetime.get_today(), -1)
            },
            {
                label: 'To Date',
                fieldname: 'to_date',
                fieldtype: 'Date',
                default: frappe.datetime.get_today()
            }
        ],
        primary_action_label: __('Get Summary'),
        primary_action: function(values) {
            get_commission_summary(frm, values.from_date, values.to_date);
            dialog.hide();
        }
    });
    
    dialog.show();
}

function get_commission_summary(frm, from_date, to_date) {
    frappe.call({
        method: 'dlitscustom.utils.commission_management_dlits.get_sales_partner_commission_summary',
        args: {
            sales_partner: frm.doc.name,
            from_date: from_date,
            to_date: to_date
        },
        callback: function(r) {
            if (r.message) {
                let summary = r.message;
                
                // Get detailed commission breakdown
                frappe.call({
                    method: 'dlitscustom.utils.commission_management_dlits.get_sales_partner_commission_details',
                    args: {
                        sales_partner: frm.doc.name,
                        from_date: from_date,
                        to_date: to_date
                    },
                    callback: function(details_r) {
                        let transactions = details_r.message || [];
                        
                        // Get payment history
                        frappe.call({
                            method: 'dlitscustom.utils.commission_management_dlits.get_sales_partner_payment_history',
                            args: {
                                sales_partner: frm.doc.name,
                                from_date: from_date,
                                to_date: to_date
                            },
                            callback: function(payments_r) {
                                let payments = payments_r.message || [];
                                
                                let html = `
                                    <div class="commission-summary">
                                        <h4>Commission Summary for ${frm.doc.partner_name || frm.doc.name}</h4>
                                        <div class="row">
                                            <div class="col-md-6">
                                                <h5>Commission Overview</h5>
                                                <table class="table table-bordered">
                                                    <tr><td><strong>Total Commission:</strong></td><td>${format_currency(summary.total_commission)}</td></tr>
                                                    <tr><td><strong>Paid Commission:</strong></td><td>${format_currency(summary.paid_commission)}</td></tr>
                                                    <tr><td><strong>Outstanding Commission:</strong></td><td>${format_currency(summary.outstanding_commission)}</td></tr>
                                                </table>
                                                
                                                <h5>Sales Overview</h5>
                                                <table class="table table-bordered">
                                                    <tr><td><strong>Total Orders:</strong></td><td>${summary.total_orders}</td></tr>
                                                    <tr><td><strong>Total Sales:</strong></td><td>${format_currency(summary.total_sales)}</td></tr>
                                                    <tr><td><strong>Commission Rate:</strong></td><td>${summary.commission_rate}%</td></tr>
                                                    <tr><td><strong>Linked Supplier:</strong></td><td>${summary.linked_supplier || 'Not Linked'}</td></tr>
                                                </table>
                                            </div>
                                            <div class="col-md-6">
                                                <h5>Linked Sales Invoices</h5>
                                                <div style="max-height: 200px; overflow-y: auto;">
                                                    <table class="table table-striped table-sm">
                                                        <thead>
                                                            <tr>
                                                                <th>Document</th>
                                                                <th>Date</th>
                                                                <th>Customer</th>
                                                                <th>Amount</th>
                                                                <th>Commission</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>`;
                                
                                if (transactions.length > 0) {
                                    transactions.forEach(function(txn) {
                                        html += `
                                            <tr>
                                                <td><a href="/app/${txn.document_type.toLowerCase().replace(' ', '-')}/${txn.name}" target="_blank">${txn.name}</a></td>
                                                <td>${frappe.datetime.str_to_user(txn.transaction_date)}</td>
                                                <td>${txn.customer}</td>
                                                <td>${format_currency(txn.base_grand_total)}</td>
                                                <td>${format_currency(txn.total_commission)}</td>
                                            </tr>`;
                                    });
                                } else {
                                    html += '<tr><td colspan="5" class="text-center">No transactions found</td></tr>';
                                }
                                
                                html += `
                                                        </tbody>
                                                    </table>
                                                </div>
                                                
                                                <h5>Linked Payment Entries</h5>
                                                <div style="max-height: 150px; overflow-y: auto;">
                                                    <table class="table table-striped table-sm">
                                                        <thead>
                                                            <tr>
                                                                <th>Payment Entry</th>
                                                                <th>Date</th>
                                                                <th>Amount</th>
                                                                <th>Type</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>`;
                                
                                if (payments.length > 0) {
                                    payments.forEach(function(payment) {
                                        html += `
                                            <tr>
                                                <td><a href="/app/payment-entry/${payment.name}" target="_blank">${payment.name}</a></td>
                                                <td>${frappe.datetime.str_to_user(payment.reference_date)}</td>
                                                <td>${format_currency(payment.paid_amount)}</td>
                                                <td><span class="badge badge-info">${payment.payment_type}</span></td>
                                            </tr>`;
                                    });
                                } else {
                                    html += '<tr><td colspan="4" class="text-center">No payments found</td></tr>';
                                }
                                
                                html += `
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                `;
                                
                                // Create a larger dialog for the enhanced summary
                                let summary_dialog = new frappe.ui.Dialog({
                                    title: __('Commission Summary for {0}', [frm.doc.partner_name || frm.doc.name]),
                                    size: 'extra-large',
                                    fields: [
                                        {
                                            fieldtype: 'HTML',
                                            fieldname: 'summary_html',
                                            options: html
                                        }
                                    ],
                                    primary_action_label: __('Close'),
                                    primary_action: function() {
                                        summary_dialog.hide();
                                    }
                                });
                                
                                summary_dialog.show();
                            }
                        });
                    }
                });
            }
        }
    });
}

function create_quick_payment(frm, amount) {
    frappe.prompt([
        {
            label: 'Pay From Account',
            fieldname: 'paid_from_account',
            fieldtype: 'Link',
            options: 'Account',
            get_query: function() {
                return {
                    filters: {
                        'account_type': ['in', ['Cash', 'Bank']],
                        'is_group': 0,
                        'company': frappe.defaults.get_user_default('Company')
                    }
                };
            },
            description: 'Select the account to pay from (Cash/Bank account)',
            reqd: 1
        }
    ], function(values) {
        frappe.call({
            method: 'dlitscustom.dlitscustom.doctype.dlits_sales_partner.dlits_sales_partner.create_commission_payment',
            args: {
                sales_partner: frm.doc.name,
                amount: amount,
                reference_doc: 'Full Outstanding Payment',
                paid_from_account: values.paid_from_account
            },
            callback: function(r) {
                if (r.message && r.message.payment_entry) {
                    frappe.msgprint(__('Payment entry created successfully'));
                    
                    // Ask if user wants to open the payment entry
                    frappe.confirm(__('Do you want to open the payment entry?'), function() {
                        frappe.set_route('Form', 'Payment Entry', r.message.payment_entry.name);
                    });
                    
                    // Update totals and refresh
                    update_commission_totals(frm);
                }
            }
        });
    }, __('Select Payment Account'), __('Create Payment'));
}

function create_partial_payment(frm) {
    let outstanding = frm.doc.outstanding_commission;
    let suggested_amounts = [
        outstanding * 0.25,
        outstanding * 0.5,
        outstanding * 0.75
    ];
    
    frappe.prompt([
        {
            label: 'Payment Amount',
            fieldname: 'amount',
            fieldtype: 'Currency',
            default: outstanding * 0.5,
            reqd: 1,
            description: `Outstanding: ${format_currency(outstanding)}`
        },
        {
            label: 'Quick Select',
            fieldname: 'quick_select',
            fieldtype: 'Select',
            options: [
                '',
                `25% (${format_currency(suggested_amounts[0])})`,
                `50% (${format_currency(suggested_amounts[1])})`,
                `75% (${format_currency(suggested_amounts[2])})`,
                `100% (${format_currency(outstanding)})`
            ],
            change: function() {
                let dialog = this.dialog;
                let value = dialog.get_value('quick_select');
                if (value) {
                    let percentage = value.split('%')[0];
                    let amount = outstanding * (parseInt(percentage) / 100);
                    dialog.set_value('amount', amount);
                }
            }
        },
        {
            label: 'Pay From Account',
            fieldname: 'paid_from_account',
            fieldtype: 'Link',
            options: 'Account',
            get_query: function() {
                return {
                    filters: {
                        'account_type': ['in', ['Cash', 'Bank']],
                        'is_group': 0,
                        'company': frappe.defaults.get_user_default('Company')
                    }
                };
            },
            description: 'Select the account to pay from (Cash/Bank account)',
            reqd: 1
        },
        {
            label: 'Reference',
            fieldname: 'reference',
            fieldtype: 'Data',
            description: 'Optional reference for this payment'
        }
    ], function(values) {
        if (values.amount > outstanding) {
            frappe.msgprint(__('Payment amount cannot exceed outstanding commission'));
            return;
        }
        
        frappe.call({
            method: 'dlitscustom.dlitscustom.doctype.dlits_sales_partner.dlits_sales_partner.create_commission_payment',
            args: {
                sales_partner: frm.doc.name,
                amount: values.amount,
                reference_doc: values.reference || 'Partial Payment',
                paid_from_account: values.paid_from_account
            },
            callback: function(r) {
                if (r.message && r.message.payment_entry) {
                    frappe.msgprint(__('Partial payment entry created successfully'));
                    
                    // Ask if user wants to open the payment entry
                    frappe.confirm(__('Do you want to open the payment entry?'), function() {
                        frappe.set_route('Form', 'Payment Entry', r.message.payment_entry.name);
                    });
                    
                    // Update totals
                    update_commission_totals(frm);
                }
            }
        });
    }, __('Create Partial Payment'), __('Create'));
}

function create_supplier_for_partner(frm) {
    frappe.confirm(__('Create a new supplier for this sales partner?'), function() {
        frappe.call({
            method: 'dlitscustom.dlitscustom.doctype.dlits_sales_partner.dlits_sales_partner.create_supplier',
            args: {
                sales_partner: frm.doc.name
            },
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint(__('Supplier created successfully'));
                    frm.reload_doc();
                }
            }
        });
    });
}

function create_commission_journal_entry(frm) {
    let outstanding = frm.doc.outstanding_commission;
    
    frappe.prompt([
        {
            label: 'Journal Entry Amount',
            fieldname: 'amount',
            fieldtype: 'Currency',
            default: outstanding,
            reqd: 1,
            description: `Outstanding Commission: ${format_currency(outstanding)}`
        },
        {
            label: 'Reference',
            fieldname: 'reference',
            fieldtype: 'Data',
            description: 'Optional reference for this journal entry'
        },
        {
            label: 'Posting Date',
            fieldname: 'posting_date',
            fieldtype: 'Date',
            default: frappe.datetime.get_today(),
            reqd: 1
        }
    ], function(values) {
        if (values.amount > outstanding) {
            frappe.msgprint(__('Journal entry amount cannot exceed outstanding commission'));
            return;
        }
        
        frappe.call({
            method: 'dlitscustom.dlitscustom.doctype.dlits_sales_partner.dlits_sales_partner.create_commission_journal_entry',
            args: {
                sales_partner: frm.doc.name,
                amount: values.amount,
                reference_doc: values.reference || 'Commission Accrual',
                posting_date: values.posting_date
            },
            callback: function(r) {
                if (r.message && r.message.journal_entry) {
                    frappe.msgprint(__('Journal entry created successfully'));
                    
                    // Ask if user wants to open the journal entry
                    frappe.confirm(__('Do you want to open the journal entry?'), function() {
                        frappe.set_route('Form', 'Journal Entry', r.message.journal_entry.name);
                    });
                    
                    // Update totals
                    update_commission_totals(frm);
                }
            }
        });
    }, __('Create Commission Journal Entry'), __('Create'));
}

function view_payment_history(frm) {
    frappe.set_route('List', 'Payment Entry', {
        'party_type': 'Supplier',
        'party': frm.doc.supplier,
        'docstatus': 1
    });
}

function update_commission_display(frm) {
    // Add visual indicators for commission status
    if (frm.doc.outstanding_commission > 0) {
        frm.dashboard.add_indicator(__('Outstanding Commission: {0}', [format_currency(frm.doc.outstanding_commission)]), 'orange');
    } else if (frm.doc.total_commission_earned > 0) {
        frm.dashboard.add_indicator(__('All Commissions Paid'), 'green');
    }
    
    if (frm.doc.status === 'Active') {
        frm.dashboard.add_indicator(__('Active Partner'), 'green');
    } else if (frm.doc.status === 'Inactive') {
        frm.dashboard.add_indicator(__('Inactive Partner'), 'red');
    } else if (frm.doc.status === 'Suspended') {
        frm.dashboard.add_indicator(__('Suspended Partner'), 'yellow');
    }
    
    // Add commission rate indicator
    if (frm.doc.commission_rate) {
        let rate_text = frm.doc.commission_type === 'Percentage'
            ? `${frm.doc.commission_rate}%`
            : format_currency(frm.doc.commission_rate);
        frm.dashboard.add_indicator(__('Commission Rate: {0}', [rate_text]), 'blue');
    }
}

// Utility function to format currency
function format_currency(amount) {
    return frappe.format(amount, {fieldtype: 'Currency'});
}
function fix_existing_commission_payments(frm) {
    frappe.confirm(__('This will update commission status for existing payments. Continue?'), function() {
        frappe.call({
            method: 'dlitscustom.dlitscustom.doctype.dlits_sales_partner.dlits_sales_partner.update_existing_commission_payments',
            args: {
                sales_partner: frm.doc.name
            },
            callback: function(r) {
                if (r.message && !r.message.error) {
                    frappe.msgprint(r.message.message);
                    frm.reload_doc();
                } else if (r.message && r.message.error) {
                    frappe.msgprint(__('Error: {0}', [r.message.error]));
                }
            }
        });
    });
}