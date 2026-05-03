// ── Dlits Customer Followup — List View ──────────────────────────────────────

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

frappe.listview_settings['Dlits Customer Followup'] = {

    add_fields: [
        'customer', 'task_title', 'task_status', 'priority', 'owned_by',
        'last_contact_date', 'aging_days', 'next_followup_date',
        'total_interactions', 'last_outcome', 'is_payment_followup',
        'agreed_payment_amount', 'total_outstanding', 'total_linked_balance'
    ],

    // ── Column formatters ─────────────────────────────────────────────────
    formatters: {

        // Status — single colorful pill column (replaces get_indicator dot)
        task_status: function(value) {
            if (!value) return '';
            let cls = STATUS_COLORS[value] || 'gray';
            return `<span class="indicator-pill ${cls} no-margin"
                style="font-size:11px;font-weight:600;padding:2px 8px;">
                ${__(value)}</span>`;
        },

        // Priority — colored pill
        priority: function(value) {
            if (!value) return '';
            const cls_map = {
                'Low':    'gray',
                'Medium': 'yellow',
                'High':   'orange',
                'Urgent': 'red'
            };
            let cls = cls_map[value] || 'gray';
            return `<span class="indicator-pill ${cls} no-margin"
                style="font-size:11px;font-weight:600;">${__(value)}</span>`;
        },

        // Updates count — badge
        total_interactions: function(value) {
            if (!value && value !== 0) return '';
            let count = value || 0;
            let cls = count === 0 ? 'gray' : count >= 5 ? 'green' : 'blue';
            return `<span class="indicator-pill ${cls} no-margin"
                style="font-size:11px;font-weight:600;padding:2px 8px;">
                ${count}</span>`;
        },

        // Last Outcome — colored pill
        last_outcome: function(value) {
            if (!value) return '';
            const cls_map = {
                'Positive':      'green',
                'Neutral':       'gray',
                'Negative':      'red',
                'Needs Followup':'yellow'
            };
            let cls = cls_map[value] || 'gray';
            return `<span class="indicator-pill ${cls} no-margin"
                style="font-size:11px;font-weight:600;">${__(value)}</span>`;
        },

        // Aging — color by urgency
        aging_days: function(value) {
            if (value === null || value === undefined || value === '') return '';
            let n = parseInt(value) || 0;
            let cls;
            if (n <= 3)       cls = 'green';
            else if (n <= 7)  cls = 'yellow';
            else if (n <= 14) cls = 'orange';
            else              cls = 'red';
            return `<span class="indicator-pill ${cls} no-margin"
                style="font-size:11px;font-weight:600;">${n}d</span>`;
        },

        // Next Scheduled — highlight overdue/today
        next_followup_date: function(value) {
            if (!value) return `<span style="color:var(--text-muted);font-size:11px;">—</span>`;
            let today = frappe.datetime.get_today();
            let style, label = frappe.datetime.str_to_user(value);
            if (value < today) {
                style = 'color:var(--red);font-weight:600;font-size:12px;';
                label += ' ⚠';
            } else if (value === today) {
                style = 'color:var(--yellow-500,var(--yellow));font-weight:600;font-size:12px;';
            } else {
                style = 'color:var(--text-color);font-size:12px;';
            }
            return `<span style="${style}">${label}</span>`;
        },

        // Payment Follow-up — indicator pill
        is_payment_followup: function(value, row) {
            if (!value) return '';
            let amt = row.agreed_payment_amount
                ? frappe.format(row.agreed_payment_amount, {fieldtype:'Currency'})
                : '';
            let tip = amt ? __('Agreed: {0}', [amt]) : __('Payment Follow-up');
            return `<span class="indicator-pill blue no-margin"
                title="${tip}" style="font-size:11px;font-weight:600;">
                💰 ${__('Payment')}</span>`;
        },

        // Last Contact date
        last_contact_date: function(value) {
            if (!value) return `<span style="color:var(--text-muted);font-size:11px;">—</span>`;
            return `<span style="color:var(--text-color);font-size:12px;">
                ${frappe.datetime.str_to_user(value)}</span>`;
        }
    },

    // ── Quick row button — Add Update ─────────────────────────────────────
    button: {
        show: function(doc) {
            return !['Completed','Cancelled','No Response (Closed)'].includes(doc.task_status);
        },
        get_label: function() { return __('Add Update'); },
        get_description: function(doc) { return __('Add a followup update for {0}', [doc.customer]); },
        action: function(doc) {
            frappe.set_route('Form', 'Dlits Customer Followup', doc.name);
        }
    },

    // ── onload: column CSS + presets + bulk actions ───────────────────────
    onload: function(listview) {
        const self = listview;

        const style = document.createElement('style');
        style.textContent = `
            /* Horizontal scroll — row wider than viewport activates sticky */
            .list-result { overflow-x: auto !important; }
            .list-rows .list-row,
            .frappe-list .list-header { min-width: 1280px !important; overflow: visible !important; }

            /* ── Fixed column widths (Frappe adds fieldname as CSS class) ── */
            .list-row-col.customer,        .list-header-col.customer        { flex: 0 0 170px !important; max-width: 170px !important; }
            .list-row-col.owned_by,        .list-header-col.owned_by        { flex: 0 0 120px !important; max-width: 120px !important; }
            .list-row-col.task_status,     .list-header-col.task_status     { flex: 0 0 135px !important; max-width: 135px !important; }
            .list-row-col.priority,        .list-header-col.priority        { flex: 0 0 80px  !important; max-width: 80px  !important; }
            .list-row-col.is_payment_followup, .list-header-col.is_payment_followup { flex: 0 0 72px !important; max-width: 72px !important; }
            .list-row-col.total_interactions,  .list-header-col.total_interactions  { flex: 0 0 65px !important; max-width: 65px !important; }
            .list-row-col.last_outcome,    .list-header-col.last_outcome    { flex: 0 0 115px !important; max-width: 115px !important; }
            .list-row-col.next_followup_date,  .list-header-col.next_followup_date  { flex: 0 0 88px !important; max-width: 88px !important; }
            .list-row-col.last_contact_date,   .list-header-col.last_contact_date   { flex: 0 0 105px !important; max-width: 105px !important; }
            .list-row-col.aging_days,      .list-header-col.aging_days      { flex: 0 0 70px  !important; max-width: 70px  !important; }

            /* Pin Add Update button column to the right edge */
            .list-row .list-row-col:has(.btn-action) {
                position:   sticky    !important;
                right:      0         !important;
                background: var(--card-bg, var(--fg-color)) !important;
                z-index:    3         !important;
                border-left: 1px solid var(--border-color) !important;
                padding:    0 8px     !important;
                display:    flex      !important;
                align-items: center   !important;
            }
            .btn-action {
                display:    inline-block !important;
                visibility: visible      !important;
                opacity:    1            !important;
            }
            .list-row-activity {
                display:    flex      !important;
                visibility: visible   !important;
                opacity:    1         !important;
            }
        `;
        document.head.appendChild(style);

        // Helper: apply preset filters
        function preset(filters) {
            self.filter_area.clear();
            self.filter_area.add(filters.map(f => ['Dlits Customer Followup', ...f]));
            self.refresh();
        }

        // ── Preset buttons ────────────────────────────────────────────────
        listview.page.add_inner_button(__('My Followups'), function() {
            preset([['owned_by', '=', frappe.session.user]]);
        });

        listview.page.add_inner_button(__("Today's Tasks"), function() {
            preset([
                ['next_followup_date', '=', frappe.datetime.get_today()],
                ['task_status', 'not in', 'Completed,Cancelled,No Response (Closed)']
            ]);
        });

        listview.page.add_inner_button(__('Overdue'), function() {
            preset([
                ['next_followup_date', '<', frappe.datetime.get_today()],
                ['task_status', 'not in', 'Completed,Cancelled,No Response (Closed)']
            ]);
        });

        listview.page.add_inner_button(__('High Priority'), function() {
            preset([['priority', 'in', 'High,Urgent']]);
        });

        listview.page.add_inner_button(__('Positive Outcome'), function() {
            preset([['last_outcome', '=', 'Positive']]);
        });

        listview.page.add_inner_button(__('No Response'), function() {
            preset([['task_status', 'in', 'No Response,No Response (Closed)']]);
        });

        // ── Bulk status actions ───────────────────────────────────────────
        const bulk_statuses = [
            'Contacted', 'Needs Follow-up', 'Meeting Scheduled',
            'Proposal Sent', 'Waiting Customer Decision',
            'On Hold', 'Not Interested', 'Completed', 'Cancelled'
        ];
        bulk_statuses.forEach(function(s) {
            listview.page.add_actions_menu_item(__('Set: {0}', [s]), function() {
                bulk_set_status(listview, s);
            });
        });
    }
};

// ── Bulk status update ────────────────────────────────────────────────────────
function bulk_set_status(listview, status) {
    let selected = listview.get_checked_items();
    if (!selected.length) {
        frappe.show_alert({message: __('Select at least one record'), indicator: 'orange'}, 3);
        return;
    }
    frappe.confirm(
        __('Set status to <b>{0}</b> for {1} record(s)?', [status, selected.length]),
        function() {
            frappe.call({
                method: 'dlitscustom.dlitscustom.doctype.dlits_customer_followup'
                      + '.dlits_customer_followup.bulk_update_status',
                args: {names: selected.map(d => d.name), status: status},
                freeze: true,
                freeze_message: __('Updating…'),
                callback: function(r) {
                    listview.refresh();
                    frappe.show_alert({
                        message: __('Updated {0} record(s) to {1}', [r.message, status]),
                        indicator: 'green'
                    }, 4);
                }
            });
        }
    );
}
