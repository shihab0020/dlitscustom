frappe.ui.form.on('Quotation', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('View Followups'), function() {
                frappe.set_route('List', 'Dlits Customer Followup', {
                    'reference_doctype': 'Quotation',
                    'reference_name': frm.doc.name
                });
            }, __('Actions'));
        }
    }
});