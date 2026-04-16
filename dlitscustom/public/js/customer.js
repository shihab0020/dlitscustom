// ── Customer — Dlits Followup Integration ─────────────────────────────────────

frappe.ui.form.on('Customer', {

    refresh: function(frm) {
        if (frm.is_new()) return;

        // Followup fields are auto-managed — make them read-only in UI
        ['custom_last_followup_status', 'custom_last_followup_date', 'custom_followup_aging']
            .forEach(f => frm.set_df_property(f, 'read_only', 1));

        // ── Action buttons — grouped under "Followup" ─────────────────────
        frm.add_custom_button(__('New Followup'), function() {
            frappe.new_doc('Dlits Customer Followup', {
                customer: frm.doc.name,
                task_title: __('Followup - {0}', [frm.doc.customer_name || frm.doc.name]),
                owned_by: frappe.session.user,
                assigned_to: frappe.session.user
            });
        }, __('Followup'));

        frm.add_custom_button(__('View All Followups'), function() {
            frappe.set_route('List', 'Dlits Customer Followup', {
                customer: frm.doc.name
            });
        }, __('Followup'));

        frm.add_custom_button(__('View Payment Followups'), function() {
            frappe.set_route('List', 'Dlits Customer Followup', {
                customer: frm.doc.name,
                is_payment_followup: 1
            });
        }, __('Followup'));

        // ── Dashboard: status + aging indicators ──────────────────────────
        render_followup_indicators(frm);

        // ── Dashboard: live followup counts ───────────────────────────────
        load_followup_counts(frm);
    }
});

// ── Status + aging indicators on the dashboard ────────────────────────────────
function render_followup_indicators(frm) {
    let aging  = frm.doc.custom_followup_aging || 0;
    let status = frm.doc.custom_last_followup_status;
    let last_date = frm.doc.custom_last_followup_date;

    if (!status && !last_date) return;

    // Color the aging indicator
    let aging_color = 'green';
    if      (aging > 14) aging_color = 'red';
    else if (aging > 7)  aging_color = 'orange';
    else if (aging > 3)  aging_color = 'yellow';

    if (last_date) {
        frm.dashboard.add_indicator(
            __('Last contact: {0} ({1}d ago)', [
                frappe.datetime.str_to_user(last_date), aging
            ]),
            aging_color
        );
    }

    if (status) {
        const STATUS_COLORS = {
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
        frm.dashboard.add_indicator(
            __('Status: {0}', [status]),
            STATUS_COLORS[status] || 'gray'
        );
    }
}

// ── Live followup counts from the server ─────────────────────────────────────
function load_followup_counts(frm) {
    frappe.call({
        method: 'dlitscustom.dlitscustom.doctype.dlits_customer_followup'
              + '.dlits_customer_followup.get_customer_followup_counts',
        args: {customer: frm.doc.name},
        callback: function(r) {
            if (!r.message) return;
            let d = r.message;

            if (d.total === 0) return;

            // Total followup count
            frm.dashboard.add_indicator(
                __('Followups: {0} total', [d.total]), 'gray'
            );

            // Active (in-pipeline) followups
            if (d.active > 0) {
                frm.dashboard.add_indicator(
                    __('{0} active', [d.active]), 'blue'
                );
            }

            // Open payment followups
            if (d.payment > 0) {
                frm.dashboard.add_indicator(
                    __('{0} payment followup(s)', [d.payment]), 'orange'
                );
            }

            // Overdue followups
            if (d.overdue > 0) {
                frm.dashboard.add_indicator(
                    __('{0} overdue', [d.overdue]), 'red'
                );
            }
        }
    });
}
