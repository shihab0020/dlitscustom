// ── Purchase Receipt — Purchase Invoice Status field behaviour ─────────────────
// Options 4 & 5 are auto-set by the system; hide them from manual dropdown.

const PR_AUTO_STATUSES = [
    'Purchase Invoice Partially Completed',
    'Purchase Invoice Completed'
];

const PR_MANUAL_OPTIONS = [
    '',
    'Purchase Invoice Ready',
    'Waiting for Purchase Invoice',
    'Waiting for Invoice and Items'
].join('\n');

frappe.ui.form.on('Purchase Receipt', {
    refresh: function (frm) {
        _apply_invoice_status_behaviour(frm);
    },
    custom_invoice_status: function (frm) {
        _apply_invoice_status_behaviour(frm);
    }
});

function _apply_invoice_status_behaviour(frm) {
    if (PR_AUTO_STATUSES.includes(frm.doc.custom_invoice_status)) {
        // Auto-set value — make read-only so user cannot overwrite
        frm.set_df_property('custom_invoice_status', 'read_only', 1);
    } else {
        // Manual entry — show only the 3 manual options in the dropdown
        frm.set_df_property('custom_invoice_status', 'read_only', 0);
        frm.set_df_property('custom_invoice_status', 'options', PR_MANUAL_OPTIONS);
    }
}
