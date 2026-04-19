// ── Dlits Customer Followup — List View ──────────────────────────────────────

frappe.listview_settings['Dlits Customer Followup'] = {

    // Fetch all display fields
    add_fields: [
        'customer', 'task_title', 'task_status', 'priority', 'owned_by',
        'last_contact_date', 'aging_days', 'next_followup_date',
        'total_interactions', 'last_outcome', 'is_payment_followup',
        'agreed_payment_amount', 'total_outstanding', 'total_linked_balance'
    ],

    // ── Status indicator pill ─────────────────────────────────────────────
    get_indicator: function(doc) {
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
        return [
            __(doc.task_status),
            STATUS_COLORS[doc.task_status] || 'gray',
            'task_status,=,' + doc.task_status
        ];
    },

    // ── Column formatters ─────────────────────────────────────────────────
    formatters: {

        // Updates count — badge with icon
        total_interactions: function(value) {
            if (!value && value !== 0) return '';
            let count = value || 0;
            // use Frappe indicator classes so dark-mode is handled automatically
            let cls = count === 0 ? 'gray' : count >= 5 ? 'green' : 'blue';
            return `<span class="indicator-pill ${cls} no-margin"
                style="font-size:11px;font-weight:600;padding:2px 8px;">
                ${count}</span>`;
        },

        // Priority — Frappe indicator pill (theme-aware)
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

        // Last Outcome — Frappe indicator pill
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

        // Aging — Frappe indicator pill, colour by urgency
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

        // Next Scheduled — use CSS vars so theme is respected
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

    // ── onload: presets + bulk actions ───────────────────────────────────
    onload: function(listview) {
        const self = listview;

        // The "Add Update" button lives inside .list-row-col.hidden-xs (the last
        // data column). We pin that column to the right edge so it stays visible
        // at any zoom level / viewport width without requiring the user to scroll.
        const style = document.createElement('style');
        style.textContent = `
            /* Horizontal scroll container */
            .list-result { overflow-x: auto !important; }
            /* Enough width so columns overflow and sticky can activate */
            .list-rows .list-row { min-width: 1100px; overflow: visible !important; }
            /* Pin the column that holds our btn-action to the right edge */
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
            /* Always show the button — not just on hover */
            .btn-action {
                display:    inline-block !important;
                visibility: visible      !important;
                opacity:    1            !important;
            }
            /* Keep like/comment count visible too */
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
