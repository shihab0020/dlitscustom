// ── Sales Invoice — Dlits Followup Integration ────────────────────────────────

const SI_STATUS_COLORS = {
    'Attempting Contact':        'orange',
    'Contacted':                 'blue',
    'No Response':               'yellow',
    'Needs Follow-up':           'orange',
    'Information Sent':          'cyan',
    'Meeting Scheduled':         'blue',
    'Demo Scheduled':            'blue',
    'Requirement Gathering':     'purple',
    'Proposal Preparing':        'purple',
    'Proposal Sent':             'purple',
    'Negotiation':               'green',
    'Waiting Customer Decision': 'yellow',
    'On Hold':                   'gray',
    'Follow-up Later':           'gray',
    'Future Opportunity':        'light-blue',
    'Lost to Competitor':        'red',
    'No Budget':                 'red',
    'Not Interested':            'red',
    'Wrong Contact':             'red',
    'Project Cancelled':         'red',
    'No Response (Closed)':      'red',
    'Completed':                 'green',
    'Cancelled':                 'gray'
};

frappe.ui.form.on('Sales Invoice', {
    refresh: function(frm) {
        if (frm.is_new()) return;

        // Auto-managed fields — lock in UI
        ['custom_last_followup_status', 'custom_last_followup_date', 'custom_followup_aging_days']
            .forEach(f => frm.set_df_property(f, 'read_only', 1));

        // Followup buttons only when there is outstanding amount
        if (frm.doc.docstatus === 1 && frm.doc.outstanding_amount > 0) {
            frm.add_custom_button(__('Create Payment Followup'), function() {
                create_si_payment_followup(frm);
            }, __('Followup'));

            frm.add_custom_button(__('View Payment Followups'), function() {
                frappe.set_route('List', 'Dlits Customer Followup', {
                    customer: frm.doc.customer,
                    is_payment_followup: 1
                });
            }, __('Followup'));
        } else if (frm.doc.docstatus === 1) {
            // Fully paid — only view
            frm.add_custom_button(__('View Followups'), function() {
                frappe.set_route('List', 'Dlits Customer Followup', {
                    customer: frm.doc.customer
                });
            }, __('Followup'));
        }

        render_si_followup_dashboard(frm);
    }
});

// ── Dashboard indicators ──────────────────────────────────────────────────────
function render_si_followup_dashboard(frm) {
    let status = frm.doc.custom_last_followup_status;
    let date   = frm.doc.custom_last_followup_date;
    let aging  = frm.doc.custom_followup_aging_days || 0;

    if (!status && !date) return;

    if (date) {
        let color = aging > 14 ? 'red' : aging > 7 ? 'orange' : aging > 3 ? 'yellow' : 'green';
        frm.dashboard.add_indicator(
            __('Last followup: {0} ({1}d ago)', [frappe.datetime.str_to_user(date), aging]),
            color
        );
    }
    if (status) {
        frm.dashboard.add_indicator(
            __('Followup: {0}', [status]),
            SI_STATUS_COLORS[status] || 'gray'
        );
    }
}

// ── Create or open existing payment followup ──────────────────────────────────
function create_si_payment_followup(frm) {
    frappe.db.get_value(
        'Dlits Customer Followup',
        {
            customer: frm.doc.customer,
            is_payment_followup: 1,
            task_status: ['not in', ['Completed', 'Cancelled', 'No Response (Closed)']]
        },
        'name',
        function(r) {
            if (r && r.name) {
                frappe.confirm(
                    __('Open payment followup <b>{0}</b> already exists for this customer. Open it?', [r.name]),
                    function() {
                        frappe.set_route('Form', 'Dlits Customer Followup', r.name);
                    }
                );
            } else {
                frappe.new_doc('Dlits Customer Followup', {
                    customer:            frm.doc.customer,
                    task_title:          __('Payment Collection - {0}', [frm.doc.name]),
                    owned_by:            frappe.session.user,
                    is_payment_followup: 1,
                    task_status:         'Attempting Contact'
                });
            }
        }
    );
}
