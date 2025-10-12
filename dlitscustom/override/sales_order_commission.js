// Copyright (c) 2024, DLITS and contributors
// For license information, please see license.txt

// Sales Order Commission JavaScript

frappe.ui.form.on('Sales Order', {
    refresh: function(frm) {
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
    }
});

function set_commission_field_properties(frm) {
    // Set commission fields as read-only
    frm.set_df_property('dlits_commission_type', 'read_only', 1);
    frm.set_df_property('dlits_commission_rate', 'read_only', 1);
    frm.set_df_property('dlits_commission_amount', 'read_only', 1);
}

function get_sales_partner_commission_details(frm) {
    if (!frm.doc.dlits_sales_partner) return;
    
    frappe.call({
        method: 'dlitscustom.override.sales_order_commission.get_sales_partner_details',
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
        method: 'dlitscustom.override.sales_order_commission.calculate_commission_amount',
        args: {
            sales_partner: frm.doc.dlits_sales_partner,
            grand_total: frm.doc.grand_total
        },
        callback: function(r) {
            if (r.message) {
                frm.set_value('dlits_commission_amount', r.message);
            }
        }
    });
}

function clear_commission_fields(frm) {
    frm.set_value('dlits_commission_type', '');
    frm.set_value('dlits_commission_rate', 0);
    frm.set_value('dlits_commission_amount', 0);
}

function update_commission_display(frm) {
    // Add visual indicators for commission
    if (frm.doc.dlits_commission_amount > 0) {
        frm.dashboard.add_indicator(__('Commission Amount: {0}', [format_currency(frm.doc.dlits_commission_amount)]), 'blue');
    }
    
    if (frm.doc.dlits_sales_partner) {
        frm.dashboard.add_indicator(__('Sales Partner: {0}', [frm.doc.dlits_sales_partner]), 'green');
    }
}

// Utility function to format currency
function format_currency(amount) {
    return frappe.format(amount, {fieldtype: 'Currency'});
}

// Auto-calculate commission on form load if sales partner is set
frappe.ui.form.on('Sales Order', {
    onload: function(frm) {
        if (frm.doc.dlits_sales_partner && !frm.doc.dlits_commission_amount) {
            get_sales_partner_commission_details(frm);
        }
    }
});