frappe.ui.form.on('Payment Entry', {
    refresh: function(frm) {
        console.log('Payment Entry refresh triggered');
        console.log('Is local:', frm.doc.__islocal);
        console.log('Window data:', window.sales_partner_payment_data);
        
        // Check if we have sales partner payment data stored
        if (window.sales_partner_payment_data && frm.doc.__islocal) {
            let data = window.sales_partner_payment_data;
            console.log('Setting payment data:', data);
            
            // Set all the fields with explicit logging
            frm.set_value('payment_type', data.payment_type);
            console.log('Set payment_type:', data.payment_type);
            
            frm.set_value('party_type', data.party_type);
            console.log('Set party_type:', data.party_type);
            
            // Set party with delay to ensure party_type is processed
            setTimeout(() => {
                frm.set_value('party', data.party);
                console.log('Set party:', data.party);
                
                frm.set_value('paid_amount', data.paid_amount);
                frm.set_value('received_amount', data.received_amount);
                frm.set_value('reference_date', data.reference_date);
                frm.set_value('remarks', data.remarks);
                
                // Set mode of payment and reference details
                if (data.mode_of_payment) {
                    frm.set_value('mode_of_payment', data.mode_of_payment);
                    console.log('Set mode_of_payment:', data.mode_of_payment);
                }
                
                if (data.reference_no) {
                    frm.set_value('reference_no', data.reference_no);
                    console.log('Set reference_no:', data.reference_no);
                }
                
                // Populate Payment References child table
                if (data.sales_partner && data.paid_amount) {
                    populate_payment_references(frm, data.sales_partner, data.paid_amount);
                }
                
                console.log('All fields set, refreshing form');
                frm.refresh_fields();
                
                // Clear the stored data after successful setting
                delete window.sales_partner_payment_data;
            }, 1000);
        }
    },
    
    onload: function(frm) {
        console.log('Payment Entry onload triggered');
        
        // Also try to set data on form load
        if (window.sales_partner_payment_data && frm.doc.__islocal) {
            let data = window.sales_partner_payment_data;
            console.log('OnLoad: Setting payment data:', data);
            
            // Set payment type and party type first
            frm.set_value('payment_type', data.payment_type);
            frm.set_value('party_type', data.party_type);
            
            // Set party after a delay to ensure party_type is set first
            setTimeout(() => {
                console.log('OnLoad: Setting party after delay:', data.party);
                frm.set_value('party', data.party);
                frm.set_value('paid_amount', data.paid_amount);
                frm.set_value('received_amount', data.received_amount);
                frm.set_value('reference_date', data.reference_date);
                frm.set_value('remarks', data.remarks);
                
                // Set additional fields
                if (data.mode_of_payment) {
                    frm.set_value('mode_of_payment', data.mode_of_payment);
                }
                if (data.reference_no) {
                    frm.set_value('reference_no', data.reference_no);
                }
                
                // Refresh the form
                frm.refresh_fields();
            }, 1500);
        }
    },
    
    party_type: function(frm) {
        console.log('Party type changed to:', frm.doc.party_type);
        
        // When party type changes, check if we need to set the party
        if (window.sales_partner_payment_data && frm.doc.party_type === 'Supplier') {
            let data = window.sales_partner_payment_data;
            console.log('Party type is Supplier, setting party:', data.party);
            
            setTimeout(() => {
                frm.set_value('party', data.party);
                frm.refresh_field('party');
            }, 200);
        }
    },
    
    setup: function(frm) {
        console.log('Payment Entry setup triggered');
        
        // Try to set data during setup as well
        if (window.sales_partner_payment_data) {
            let data = window.sales_partner_payment_data;
            console.log('Setup: Found payment data:', data);
            
            // Set basic fields during setup
            frm.doc.payment_type = data.payment_type;
            frm.doc.party_type = data.party_type;
            frm.doc.party = data.party;
            frm.doc.paid_amount = data.paid_amount;
            frm.doc.received_amount = data.received_amount;
            frm.doc.reference_date = data.reference_date;
            frm.doc.remarks = data.remarks;
            
            // Set additional fields
            if (data.mode_of_payment) {
                frm.doc.mode_of_payment = data.mode_of_payment;
            }
            if (data.reference_no) {
                frm.doc.reference_no = data.reference_no;
            }
        }
    }
});

// Function to populate Payment References child table
function populate_payment_references(frm, sales_partner, commission_amount) {
    console.log('Populating payment references for:', sales_partner, 'Amount:', commission_amount);
    
    frappe.call({
        method: 'dlitscustom.utils.payment_references_dlits.get_payment_references_for_commission',
        args: {
            sales_partner: sales_partner,
            commission_amount: commission_amount,
            from_date: frappe.datetime.add_months(frappe.datetime.get_today(), -3),
            to_date: frappe.datetime.get_today()
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                console.log('Payment references received:', r.message);
                
                // Clear existing references
                frm.clear_table('references');
                
                // Add each reference to the child table
                r.message.forEach(function(ref) {
                    let row = frm.add_child('references');
                    row.reference_doctype = ref.reference_doctype;
                    row.reference_name = ref.reference_name;
                    row.due_date = ref.due_date;
                    row.total_amount = ref.total_amount;
                    row.outstanding_amount = ref.outstanding_amount;
                    row.allocated_amount = ref.allocated_amount;
                    
                    console.log('Added reference:', ref.reference_doctype, ref.reference_name);
                });
                
                // Refresh the child table
                frm.refresh_field('references');
                
                // Update total allocated amount
                let total_allocated = 0;
                frm.doc.references.forEach(function(ref) {
                    total_allocated += ref.allocated_amount || 0;
                });
                
                frm.set_value('total_allocated_amount', total_allocated);
                
                console.log('Payment references populated successfully. Total allocated:', total_allocated);
            } else {
                console.log('No payment references found');
                frappe.msgprint(__('No outstanding commission references found. You may need to create a Journal Entry manually.'));
            }
        },
        error: function(r) {
            console.error('Error fetching payment references:', r);
            frappe.msgprint(__('Error fetching payment references. Please check the console for details.'));
        }
    });
}