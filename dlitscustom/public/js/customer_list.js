// ── Customer List — Dlits Followup Status Formatters ─────────────────────────
// Extends (does NOT replace) any existing ERPNext Customer listview settings.

frappe.provide('frappe.listview_settings');

(function () {
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

    // Merge into existing settings (ERPNext may have already set this)
    const s = frappe.listview_settings['Customer'] || {};

    // Extend add_fields without duplicates
    const af = s.add_fields ? s.add_fields.slice() : [];
    ['custom_last_followup_status', 'custom_last_followup_date', 'custom_followup_aging']
        .forEach(function (f) { if (!af.includes(f)) af.push(f); });
    s.add_fields = af;

    // Merge formatters
    s.formatters = Object.assign(s.formatters || {}, {

        custom_last_followup_status: function (value) {
            if (!value) return '';
            const cls = STATUS_COLORS[value] || 'gray';
            return `<span class="indicator-pill ${cls} no-margin"
                style="font-size:11px;font-weight:600;padding:2px 8px;">${__(value)}</span>`;
        },

        custom_last_followup_date: function (value, row) {
            if (!value) return `<span style="color:var(--text-muted);font-size:11px;">—</span>`;
            const aging = row.custom_followup_aging || 0;
            let color = aging > 14 ? 'var(--red)' : aging > 7 ? 'var(--orange)' : 'var(--text-color)';
            const label = frappe.datetime.str_to_user(value);
            return `<span style="font-size:12px;color:${color};">${label}</span>`;
        }
    });

    frappe.listview_settings['Customer'] = s;
})();
