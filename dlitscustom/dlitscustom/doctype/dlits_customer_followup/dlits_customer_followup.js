// ── Dlits Customer Followup — Form ────────────────────────────────────────────

frappe.ui.form.on('Dlits Customer Followup', {

    onload: function(frm) {
        if (frm.doc.customer) set_contact_query(frm);
    },

    refresh: function(frm) {
        if (frm.doc.customer) set_contact_query(frm);

        render_summary_bar(frm);

        if (!frm.is_new()) {
            setup_action_buttons(frm);
        }

        // Refresh payment data on every open if payment followup
        if (frm.doc.is_payment_followup && frm.doc.customer) {
            fetch_customer_outstanding(frm);
            render_invoice_list(frm);
        }

        // Refresh linked balance in case rows were saved
        recalc_linked_balance(frm);
    },

    // ── Field events ─────────────────────────────────────────────────────────
    customer: function(frm) {
        if (frm.doc.customer) {
            set_contact_query(frm);
            frm.set_value('contact_person', '');
            show_customer_history(frm);
            if (frm.doc.is_payment_followup) {
                fetch_customer_outstanding(frm);
                render_invoice_list(frm);
            }
        } else {
            frm.set_value('contact_person', '');
            frm.set_value('total_outstanding', 0);
            clear_invoice_list(frm);
        }
    },

    is_payment_followup: function(frm) {
        if (frm.doc.is_payment_followup && frm.doc.customer) {
            fetch_customer_outstanding(frm);
            render_invoice_list(frm);
        } else {
            frm.set_value('total_outstanding', 0);
            clear_invoice_list(frm);
        }
    },

    task_status: function(frm) {
        const done = ['Completed', 'Cancelled', 'No Response (Closed)',
                      'Lost to Competitor', 'Not Interested', 'No Budget'];
        if (frm.doc.task_status === 'Completed') {
            frappe.show_alert({message: __('Followup marked as completed'), indicator: 'green'}, 5);
        } else if (done.includes(frm.doc.task_status)) {
            frappe.show_alert({message: __('Status: {0}', [frm.doc.task_status]), indicator: 'orange'}, 4);
        }
    }
});

// ── Child table: Followup Updates ─────────────────────────────────────────────
frappe.ui.form.on('Dlits Followup Update', {
    followup_updates_add: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.update_date = frappe.datetime.now_datetime();
        row.contacted_by = frappe.session.user;
        row.followup_type = 'Phone Call';
        frm.refresh_field('followup_updates');
    },

    duration_minutes: function(frm) {
        let total = (frm.doc.followup_updates || []).reduce((s, d) => s + (d.duration_minutes || 0), 0);
        if (total > 0) {
            frm.set_intro(__('Total contact time: {0} minutes', [total]), 'blue');
        }
    },

    outcome: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.outcome === 'Positive') {
            frappe.show_alert({message: __('Positive outcome recorded'), indicator: 'green'}, 3);
        } else if (row.outcome === 'Negative') {
            frappe.show_alert({message: __('Negative outcome recorded'), indicator: 'red'}, 3);
        }
    }
});

// ── Child table: Linked Documents ─────────────────────────────────────────────
frappe.ui.form.on('Dlits Followup Linked Document', {
    document_type: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, 'document_name', '');
        frappe.model.set_value(cdt, cdn, 'amount', 0);
        frappe.model.set_value(cdt, cdn, 'paid_amount', 0);
        frappe.model.set_value(cdt, cdn, 'balance_amount', 0);
        recalc_linked_balance(frm);

        if (row.document_type && frm.doc.customer) {
            frm.fields_dict['linked_documents'].grid.get_field('document_name').get_query =
                function(doc, cdt, cdn) {
                    let r = locals[cdt][cdn];
                    let filters = {};
                    if (['Quotation', 'Opportunity'].includes(r.document_type)) {
                        filters = {party_name: frm.doc.customer, docstatus: 1};
                    } else if (['Sales Order', 'Sales Invoice', 'Delivery Note'].includes(r.document_type)) {
                        filters = {customer: frm.doc.customer, docstatus: 1};
                    } else if (r.document_type === 'Payment Entry') {
                        filters = {party: frm.doc.customer, party_type: 'Customer', docstatus: 1};
                    }
                    return {filters: filters};
                };
            frm.refresh_field('linked_documents');
        }
    },

    document_name: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.document_type && row.document_name) {
            frappe.call({
                method: 'dlitscustom.dlitscustom.doctype.dlits_customer_followup'
                      + '.dlits_customer_followup.get_document_amounts',
                args: {doctype: row.document_type, docname: row.document_name},
                callback: function(r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'amount',         r.message.amount);
                        frappe.model.set_value(cdt, cdn, 'paid_amount',    r.message.paid_amount);
                        frappe.model.set_value(cdt, cdn, 'balance_amount', r.message.balance_amount);
                        frm.refresh_field('linked_documents');
                        recalc_linked_balance(frm);
                    }
                }
            });
        }
    },

    linked_documents_remove: function(frm) {
        recalc_linked_balance(frm);
    }
});

// ── Action buttons setup ──────────────────────────────────────────────────────
function setup_action_buttons(frm) {
    // Primary: Add Update — opens a quick dialog
    frm.add_custom_button(__('Add Update'), function() {
        open_add_update_dialog(frm);
    }).css({'background-color': '#2490ef', 'color': '#fff', 'font-weight': '600'});

    // Mark Completed
    if (!['Completed', 'Cancelled'].includes(frm.doc.task_status)) {
        frm.add_custom_button(__('Mark Completed'), function() {
            frappe.confirm(__('Mark this followup as completed?'), function() {
                frm.set_value('task_status', 'Completed');
                frm.save();
            });
        });
    }

    // Set Status shortcuts
    const quick_statuses = [
        'Contacted', 'Needs Follow-up', 'Meeting Scheduled',
        'Proposal Sent', 'Waiting Customer Decision',
        'On Hold', 'Not Interested'
    ];
    quick_statuses.forEach(function(s) {
        frm.add_custom_button(__(s), function() {
            frm.set_value('task_status', s);
            frm.save();
        }, __('Set Status'));
    });
}

// ── Add Update dialog ─────────────────────────────────────────────────────────
function open_add_update_dialog(frm) {
    let fields = [
        {
            fieldname: 'followup_type', fieldtype: 'Select', label: __('Contact Type'), reqd: 1,
            options: 'Phone Call\nEmail\nMeeting\nWhatsApp\nSMS\nVideo Call',
            default: 'Phone Call'
        },
        {fieldname: 'col1', fieldtype: 'Column Break'},
        {
            fieldname: 'status', fieldtype: 'Select', label: __('Contact Status'),
            options: 'Attempted\nSpoke\nAnswered\nLeft Message\nNo Answer\nEmail Sent',
            default: 'Attempted'
        },
        {fieldname: 'sec1', fieldtype: 'Section Break', label: __('Details')},
        {
            fieldname: 'duration_minutes', fieldtype: 'Int',
            label: __('Duration (Min)')
        },
        {fieldname: 'col2', fieldtype: 'Column Break'},
        {
            fieldname: 'outcome', fieldtype: 'Select', label: __('Outcome'),
            options: '\nPositive\nNeutral\nNegative\nNeeds Followup'
        },
        {fieldname: 'sec2', fieldtype: 'Section Break'},
        {
            fieldname: 'discussion_summary', fieldtype: 'Small Text',
            label: __('Discussion Summary'), reqd: 1
        },
        {fieldname: 'col3', fieldtype: 'Column Break'},
        {fieldname: 'next_action', fieldtype: 'Data', label: __('Next Action')}
    ];

    // Payment amount field if payment followup
    if (frm.doc.is_payment_followup) {
        fields.push({fieldname: 'sec_pay', fieldtype: 'Section Break', label: __('Payment')});
        fields.push({
            fieldname: 'agreed_payment_amount', fieldtype: 'Currency',
            label: __('Agreed Payment Amount')
        });
    }

    let d = new frappe.ui.Dialog({
        title: __('Add Followup Update — {0}', [frm.doc.customer || '']),
        fields: fields,
        primary_action_label: __('Save Update'),
        primary_action: function(vals) {
            let row = frm.add_child('followup_updates');
            row.update_date         = frappe.datetime.now_datetime();
            row.contacted_by        = frappe.session.user;
            row.followup_type       = vals.followup_type;
            row.status              = vals.status;
            row.duration_minutes    = vals.duration_minutes;
            row.outcome             = vals.outcome;
            row.discussion_summary  = vals.discussion_summary;
            row.next_action         = vals.next_action;
            if (frm.doc.is_payment_followup && vals.agreed_payment_amount) {
                row.agreed_payment_amount = vals.agreed_payment_amount;
            }
            frm.refresh_field('followup_updates');
            render_summary_bar(frm);
            frm.save();
            d.hide();
            frappe.show_alert({message: __('Update added'), indicator: 'green'}, 3);
        }
    });
    d.show();
}

// ── Summary bar above followup updates ───────────────────────────────────────
function render_summary_bar(frm) {
    let updates = frm.doc.followup_updates || [];
    if (!updates.length) {
        frm.set_df_property('followup_updates', 'description', '');
        return;
    }
    let total_dur = 0, pos = 0, neu = 0, neg = 0;
    updates.forEach(function(u) {
        total_dur += (u.duration_minutes || 0);
        if (u.outcome === 'Positive')      pos++;
        else if (u.outcome === 'Neutral')  neu++;
        else if (u.outcome === 'Negative') neg++;
    });
    let html = `<div style="padding:6px 12px;background:#f0f4f8;border-left:3px solid #2490ef;
        border-radius:3px;font-size:12px;margin-bottom:4px;">
        <b>${updates.length}</b> interactions &nbsp;|&nbsp;
        <b>${total_dur}</b> min total &nbsp;|&nbsp;
        <span style="color:#198754;font-weight:600;">&#10003; ${pos} positive</span> &nbsp;
        <span style="color:#6c757d;">&#126; ${neu} neutral</span> &nbsp;
        <span style="color:#dc3545;font-weight:600;">&#10007; ${neg} negative</span>
    </div>`;
    frm.set_df_property('followup_updates', 'description', html);
}

// ── Customer history on dashboard ────────────────────────────────────────────
function show_customer_history(frm) {
    frappe.call({
        method: 'frappe.client.get_value',
        args: {
            doctype: 'Customer',
            filters: {name: frm.doc.customer},
            fieldname: ['custom_last_followup_status', 'custom_last_followup_date', 'custom_followup_aging']
        },
        callback: function(r) {
            if (r.message && r.message.custom_last_followup_date) {
                frm.dashboard.add_comment(
                    __('Last contact: {0} ({1} days ago) — Status: {2}', [
                        frappe.datetime.str_to_user(r.message.custom_last_followup_date),
                        r.message.custom_followup_aging || 0,
                        r.message.custom_last_followup_status || '—'
                    ]),
                    'blue', true
                );
            }
        }
    });
}

// ── Payment: fetch outstanding ────────────────────────────────────────────────
function fetch_customer_outstanding(frm) {
    frappe.call({
        method: 'dlitscustom.dlitscustom.doctype.dlits_customer_followup'
              + '.dlits_customer_followup.get_customer_outstanding',
        args: {customer: frm.doc.customer},
        callback: function(r) {
            if (r.message !== undefined) {
                frm.set_value('total_outstanding', r.message);
            }
        }
    });
}

// ── Payment: render outstanding invoice table ─────────────────────────────────
function render_invoice_list(frm) {
    if (!frm.doc.customer) return;
    let wrapper = frm.get_field('payment_invoices_html');
    if (!wrapper) return;

    frappe.call({
        method: 'dlitscustom.dlitscustom.doctype.dlits_customer_followup'
              + '.dlits_customer_followup.get_customer_invoices',
        args: {customer: frm.doc.customer},
        callback: function(r) {
            let invoices = r.message || [];
            if (!invoices.length) {
                wrapper.$wrapper.html(
                    `<p style="color:var(--text-muted);font-size:12px;margin:4px 0;">
                        ${__('No outstanding invoices.')}
                    </p>`
                );
                return;
            }
            let rows = invoices.map(function(inv) {
                let overdue_badge = '';
                if (inv.overdue_days > 0) {
                    overdue_badge = `<span class="indicator-pill red no-margin"
                        style="margin-left:5px;font-size:10px;">
                        ${inv.overdue_days}d overdue</span>`;
                }
                let due_date_html = inv.due_date
                    ? frappe.datetime.str_to_user(inv.due_date)
                    : '—';
                // highlight due-date cell if overdue
                let due_style = inv.overdue_days > 0
                    ? 'color:var(--red);font-weight:600;'
                    : 'color:var(--text-color);';
                return `<tr style="border-bottom:1px solid var(--border-color);">
                    <td style="padding:5px 8px;">
                        <a href="/app/sales-invoice/${inv.name}" target="_blank"
                           style="color:var(--primary);font-size:12px;">${inv.name}</a>
                        ${overdue_badge}
                    </td>
                    <td style="padding:5px 8px;font-size:12px;color:var(--text-color);">
                        ${frappe.datetime.str_to_user(inv.posting_date)}
                    </td>
                    <td style="padding:5px 8px;font-size:12px;${due_style}">
                        ${due_date_html}
                    </td>
                    <td style="padding:5px 8px;font-size:12px;text-align:right;color:var(--text-color);">
                        ${frappe.format(inv.grand_total, {fieldtype:'Currency'})}
                    </td>
                    <td style="padding:5px 8px;font-size:12px;text-align:right;
                               color:var(--red);font-weight:600;">
                        ${frappe.format(inv.outstanding_amount, {fieldtype:'Currency'})}
                    </td>
                </tr>`;
            }).join('');

            wrapper.$wrapper.html(`
                <div style="margin-top:6px;overflow-x:auto;border:1px solid var(--border-color);
                            border-radius:var(--border-radius-md,4px);">
                    <table style="width:100%;border-collapse:collapse;">
                        <thead>
                            <tr style="background:var(--subtle-bg);
                                       border-bottom:2px solid var(--border-color);">
                                <th style="padding:6px 8px;text-align:left;font-size:11px;
                                           font-weight:600;color:var(--text-muted);
                                           text-transform:uppercase;letter-spacing:.4px;">
                                    ${__('Invoice')}
                                </th>
                                <th style="padding:6px 8px;text-align:left;font-size:11px;
                                           font-weight:600;color:var(--text-muted);
                                           text-transform:uppercase;letter-spacing:.4px;">
                                    ${__('Date')}
                                </th>
                                <th style="padding:6px 8px;text-align:left;font-size:11px;
                                           font-weight:600;color:var(--text-muted);
                                           text-transform:uppercase;letter-spacing:.4px;">
                                    ${__('Due Date')}
                                </th>
                                <th style="padding:6px 8px;text-align:right;font-size:11px;
                                           font-weight:600;color:var(--text-muted);
                                           text-transform:uppercase;letter-spacing:.4px;">
                                    ${__('Amount')}
                                </th>
                                <th style="padding:6px 8px;text-align:right;font-size:11px;
                                           font-weight:600;color:var(--text-muted);
                                           text-transform:uppercase;letter-spacing:.4px;">
                                    ${__('Outstanding')}
                                </th>
                            </tr>
                        </thead>
                        <tbody>${rows}</tbody>
                    </table>
                </div>`);
        }
    });
}

function clear_invoice_list(frm) {
    let wrapper = frm.get_field('payment_invoices_html');
    if (wrapper) wrapper.$wrapper.html('');
}

// ── Linked balance recalculation ──────────────────────────────────────────────
function recalc_linked_balance(frm) {
    let total = (frm.doc.linked_documents || []).reduce((s, r) => s + (r.balance_amount || 0), 0);
    frm.set_value('total_linked_balance', total);
}

// ── Contact person query ──────────────────────────────────────────────────────
function set_contact_query(frm) {
    frm.set_query('contact_person', function() {
        return {
            query: 'frappe.contacts.doctype.contact.contact.contact_query',
            filters: {link_doctype: 'Customer', link_name: frm.doc.customer}
        };
    });
}
