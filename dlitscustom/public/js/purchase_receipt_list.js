// ── Purchase Receipt List — Invoice Status Indicator ─────────────────────────

frappe.provide('frappe.listview_settings');

(function () {
    const STATUS_COLORS = {
        'Purchase Invoice Ready':              'green',
        'Waiting for Purchase Invoice':        'orange',
        'Waiting for Invoice and Items':       'red',
        'Purchase Invoice Partially Completed':'blue',
        'Purchase Invoice Completed':          'green'
    };

    const s = frappe.listview_settings['Purchase Receipt'] || {};

    const af = s.add_fields ? s.add_fields.slice() : [];
    if (!af.includes('custom_invoice_status')) af.push('custom_invoice_status');
    s.add_fields = af;

    s.formatters = Object.assign(s.formatters || {}, {
        custom_invoice_status: function (value) {
            if (!value) return '';
            const cls = STATUS_COLORS[value] || 'gray';
            return `<span class="indicator-pill ${cls} no-margin"
                style="font-size:11px;font-weight:600;padding:2px 8px;">${__(value)}</span>`;
        }
    });

    frappe.listview_settings['Purchase Receipt'] = s;
})();
