// Copyright (c) 2024, DLITS and contributors
// For license information, please see license.txt

// Sales Invoice Commission JavaScript

frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        // Add commission-related buttons
        add_commission_buttons(frm);
        
        // Set field properties
        set_commission_field_properties(frm);
        
        // Update commission display
        update_commission_display(frm);
    },
    
    dlits_sales_partner: function(frm) {
        // When sales partner is selected, get commission details and calculate
        if (frm.doc.dlits_sales_partner) {
            get_sales_partner_commission_details(frm);
        } else {
            clear_commission_fields(frm);
        }
    },
    
    grand_total: function(frm) {
        // Recalculate commission when grand total changes
        if (frm.doc.dlits_sales_partner && frm.doc.grand_total) {
            calculate_commission_amount(frm);
        }
    },
    
    dlits_commission_paid_amount: function(frm) {
        // Update outstanding commission when paid amount changes
        update_outstanding_commission(frm);
    }
});

function add_commission_buttons(frm) {
    if (!frm.is_new() && frm.doc.docstatus === 1) {
        
        // Update Commission Paid button
        if (frm.doc.dlits_commission_outstanding > 0) {
            frm.add_custom_button(__('Update Commission Paid'), function() {
                update_commission_paid_dialog(frm);
            }, __('Commission'));
        }
        
        // Create Commission Payment button
        if (frm.doc.dlits_commission_outstanding > 0 && frm.doc.dlits_sales_partner) {
            frm.add_custom_button(__('Create Commission Payment'), function() {
                create_commission_payment(frm);
            }, __('Commission'));
        }
        
        // View Commission Report button
        if (frm.doc.dlits_sales_partner) {
            frm.add_custom_button(__('View Commission Report'), function() {
                view_commission_report(frm);
            }, __('Commission'));
        }
    }
}

function set_commission_field_properties(frm) {
    // Set commission fields as read-only based on conditions
    frm.set_df_property('dlits_commission_type', 'read_only', 1);
    frm.set_df_property('dlits_commission_rate', 'read_only', 1);
    frm.set_df_property('dlits_commission_amount', 'read_only', 1);
    frm.set_df_property('dlits_commission_outstanding', 'read_only', 1);
    
    // Commission paid amount can be edited after submit
    if (frm.doc.docstatus === 1) {
        frm.set_df_property('dlits_commission_paid_amount', 'read_only', 0);
    }
}

function get_sales_partner_commission_details(frm) {
    if (!frm.doc.dlits_sales_partner) return;
    
    frappe.call({
        method: 'dlitscustom.override.sales_invoice_commission.get_sales_partner_details',
        args: {
            sales_partner: frm.doc.dlits_sales_partner
        },
        callback: function(r) {
            if (r.message) {
                let details = r.message;
                
                // Check if partner is active
                if (details.status !== 'Active') {
                    frappe.msgprint(__('Selected sales partner is not active'));
                    frm.set_value('dlits_sales_partner', '');
                    return;
                }
                
                // Set commission details
                frm.set_value('dlits_commission_type', details.commission_type);
                frm.set_value('dlits_commission_rate', details.commission_rate);
                
                // Calculate commission amount
                calculate_commission_amount(frm);
            }
        }
    });
}

function calculate_commission_amount(frm) {
    if (!frm.doc.dlits_sales_partner || !frm.doc.grand_total) return;
    
    frappe.call({
        method: 'dlitscustom.override.sales_invoice_commission.calculate_commission_amount',
        args: {
            sales_partner: frm.doc.dlits_sales_partner,
            grand_total: frm.doc.grand_total
        },
        callback: function(r) {
            if (r.message) {
                frm.set_value('dlits_commission_amount', r.message);
                update_outstanding_commission(frm);
            }
        }
    });
}

function update_outstanding_commission(frm) {
    let outstanding = flt(frm.doc.dlits_commission_amount) - flt(frm.doc.dlits_commission_paid_amount);
    frm.set_value('dlits_commission_outstanding', outstanding);
}

function clear_commission_fields(frm) {
    frm.set_value('dlits_commission_type', '');
    frm.set_value('dlits_commission_rate', 0);
    frm.set_value('dlits_commission_amount', 0);
    frm.set_value('dlits_commission_paid_amount', 0);
    frm.set_value('dlits_commission_outstanding', 0);
}

function update_commission_paid_dialog(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('Update Commission Paid Amount'),
        fields: [
            {
                label: 'Commission Amount',
                fieldname: 'commission_amount',
                fieldtype: 'Currency',
                default: frm.doc.dlits_commission_amount,
                read_only: 1
            },
            {
                label: 'Currently Paid',
                fieldname: 'current_paid',
                fieldtype: 'Currency',
                default: frm.doc.dlits_commission_paid_amount,
                read_only: 1
            },
            {
                label: 'New Paid Amount',
                fieldname: 'new_paid_amount',
                fieldtype: 'Currency',
                default: frm.doc.dlits_commission_paid_amount,
                reqd: 1
            },
            {
                label: 'Notes',
                fieldname: 'notes',
                fieldtype: 'Small Text',
                description: 'Optional notes for this payment update'
            }
        ],
        primary_action_label: __('Update'),
        primary_action: function(values) {
            if (flt(values.new_paid_amount) > flt(frm.doc.dlits_commission_amount)) {
                frappe.msgprint(__('Paid amount cannot be greater than commission amount'));
                return;
            }
            
            if (flt(values.new_paid_amount) < 0) {
                frappe.msgprint(__('Paid amount cannot be negative'));
                return;
            }
            
            frappe.call({
                method: 'dlitscustom.override.sales_invoice_commission.update_commission_paid_amount',
                args: {
                    invoice_name: frm.doc.name,
                    paid_amount: values.new_paid_amount
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.msgprint(r.message.message);
                        frm.reload_doc();
                    } else if (r.message) {
                        frappe.msgprint(r.message.message);
                    }
                }
            });
            
            dialog.hide();
        }
    });
    
    dialog.show();
}

function create_commission_payment(frm) {
    let outstanding = frm.doc.dlits_commission_outstanding;
    
    frappe.prompt([
        {
            label: 'Payment Amount',
            fieldname: 'amount',
            fieldtype: 'Currency',
            default: outstanding,
            reqd: 1
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
                sales_partner: frm.doc.dlits_sales_partner,
                amount: values.amount,
                reference_doc: frm.doc.name
            },
            callback: function(r) {
                if (r.message && r.message.payment_entry) {
                    frappe.msgprint(__('Payment entry created successfully'));
                    
                    // Ask if user wants to open the payment entry
                    frappe.confirm(__('Do you want to open the payment entry?'), function() {
                        frappe.set_route('Form', 'Payment Entry', r.message.payment_entry.name);
                    });
                    
                    // Update the paid amount in this invoice
                    frappe.call({
                        method: 'dlitscustom.override.sales_invoice_commission.update_commission_paid_amount',
                        args: {
                            invoice_name: frm.doc.name,
                            paid_amount: flt(frm.doc.dlits_commission_paid_amount) + flt(values.amount)
                        },
                        callback: function(r) {
                            if (r.message && r.message.success) {
                                frm.reload_doc();
                            }
                        }
                    });
                }
            }
        });
    }, __('Create Commission Payment'), __('Create'));
}

function view_commission_report(frm) {
    // Use direct URL to avoid getdoctype issues
    let url = `/app/query-report/DLITS%20Sales%20Partner%20Commission%20Report?sales_partner=${encodeURIComponent(frm.doc.dlits_sales_partner)}&from_date=${frm.doc.posting_date}&to_date=${frm.doc.posting_date}`;
    window.open(url, '_blank');
}

function update_commission_display(frm) {
    // Add visual indicators for commission status
    if (frm.doc.dlits_commission_outstanding > 0) {
        frm.dashboard.add_indicator(__('Outstanding Commission: {0}', [format_currency(frm.doc.dlits_commission_outstanding)]), 'orange');
    } else if (frm.doc.dlits_commission_amount > 0 && frm.doc.dlits_commission_outstanding === 0) {
        frm.dashboard.add_indicator(__('Commission Fully Paid'), 'green');
    }
    
    if (frm.doc.dlits_sales_partner) {
        frm.dashboard.add_indicator(__('Sales Partner: {0}', [frm.doc.dlits_sales_partner]), 'blue');
    }
}

// Utility function to format currency
function format_currency(amount) {
    return frappe.format(amount, {fieldtype: 'Currency'});
}

// Auto-calculate commission on form load if sales partner is set
frappe.ui.form.on('Sales Invoice', {
    onload: function(frm) {
        if (frm.doc.dlits_sales_partner && !frm.doc.dlits_commission_amount) {
            get_sales_partner_commission_details(frm);
        }
    }
});