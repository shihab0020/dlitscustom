// ── Standalone dialog helpers (no frm.trigger needed) ─────────────────────

function _show_additional_salary_dialog(frm, info) {
    let d = new frappe.ui.Dialog({
        title: __("Commission via Additional Salary (Payroll)"),
        fields: [
            {
                fieldname: "employee",
                label: __("Employee"),
                fieldtype: "Link",
                options: "Employee",
                default: info.employee || "",
                read_only: info.employee ? 1 : 0,
                reqd: 1,
                description: __("Employee linked to this partner's ERPNext user")
            },
            { fieldtype: "Column Break" },
            {
                fieldname: "payroll_date",
                label: __("Payroll Date"),
                fieldtype: "Date",
                default: frappe.datetime.get_today(),
                reqd: 1,
                description: __("Commission will appear in payroll for this date")
            },
            { fieldtype: "Section Break" },
            {
                fieldname: "salary_component",
                label: __("Salary Component"),
                fieldtype: "Link",
                options: "Salary Component",
                default: "Sales Commission",
                reqd: 1,
                get_query: function() { return { filters: { type: "Earning" } }; },
                description: __("Must be an Earning type component")
            },
            { fieldtype: "Column Break" },
            {
                fieldname: "amount",
                label: __("Amount"),
                fieldtype: "Currency",
                default: frm.doc.balance_commission,
                reqd: 1
            }
        ],
        primary_action_label: __("Create Additional Salary"),
        primary_action: function(vals) {
            frappe.call({
                method: "dlitscustom.dlitscustom.doctype.dlits_commission_management.dlits_commission_management.create_additional_salary_payment",
                args: {
                    name:             frm.doc.name,
                    employee:         vals.employee,
                    salary_component: vals.salary_component,
                    payroll_date:     vals.payroll_date,
                    amount:           vals.amount,
                },
                freeze: true,
                freeze_message: __("Creating Additional Salary..."),
                callback: function(r) {
                    if (!r.exc) {
                        d.hide();
                        frm.reload_doc();
                        frappe.show_alert({ message: __("Additional Salary created: {0}", [r.message]), indicator: "green" });
                    }
                }
            });
        }
    });
    d.show();
}

function _show_je_dialog(frm) {
    var company = frappe.defaults.get_user_default("Company")
                  || (frappe.boot.sysdefaults && frappe.boot.sysdefaults.default_company);
    frappe.db.get_value("Company", company, "cost_center", function(r) {
        var default_cc = (r && r.cost_center) ? r.cost_center : "";
        let d = new frappe.ui.Dialog({
            title: __("Commission Payment via Journal Entry"),
            fields: [
                {
                    fieldname: "amount",
                    label: __("Amount"),
                    fieldtype: "Currency",
                    default: frm.doc.balance_commission,
                    reqd: 1
                },
                { fieldtype: "Column Break" },
                {
                    fieldname: "payment_date",
                    label: __("Payment Date"),
                    fieldtype: "Date",
                    default: frappe.datetime.get_today(),
                    reqd: 1
                },
                { fieldtype: "Section Break", label: __("Accounts") },
                {
                    fieldname: "expense_account",
                    label: __("Commission Expense Account"),
                    fieldtype: "Link",
                    options: "Account",
                    reqd: 1,
                    get_query: function() {
                        return {
                            filters: {
                                account_name: ["in", [
                                    "Buyer Representative Incetives & Gifts",
                                    "Sales Partner Rebates & Comm."
                                ]],
                                is_group: 0
                            }
                        };
                    }
                },
                { fieldtype: "Column Break" },
                {
                    fieldname: "payment_account",
                    label: __("Pay From (Bank / Cash)"),
                    fieldtype: "Link",
                    options: "Account",
                    reqd: 1,
                    description: __("Credit — money leaves this account"),
                    get_query: function() { return { filters: { account_type: ["in", ["Bank", "Cash"]], is_group: 0 } }; }
                },
                { fieldtype: "Section Break", label: __("Cost Center & Reference") },
                {
                    fieldname: "cost_center",
                    label: __("Cost Center"),
                    fieldtype: "Link",
                    options: "Cost Center",
                    default: default_cc,
                    reqd: 1,
                    get_query: function() { return { filters: { is_group: 0 } }; }
                },
                { fieldtype: "Column Break" },
                {
                    fieldname: "cheque_no",
                    label: __("Reference / Cheque No"),
                    fieldtype: "Data"
                }
            ],
            primary_action_label: __("Create Journal Entry"),
            primary_action: function(vals) {
                frappe.call({
                    method: "dlitscustom.dlitscustom.doctype.dlits_commission_management.dlits_commission_management.create_payment_journal_entry",
                    args: {
                        name:            frm.doc.name,
                        payment_date:    vals.payment_date,
                        expense_account: vals.expense_account,
                        payment_account: vals.payment_account,
                        cost_center:     vals.cost_center,
                        amount:          vals.amount,
                        cheque_no:       vals.cheque_no || null,
                    },
                    freeze: true,
                    freeze_message: __("Creating Journal Entry..."),
                    callback: function(r) {
                        if (!r.exc) {
                            d.hide();
                            frm.reload_doc();
                            frappe.show_alert({ message: __("Journal Entry created: {0}", [r.message]), indicator: "green" });
                        }
                    }
                });
            }
        });
        d.show();
    });
}

function _show_payment_method_choice(frm, info) {
    let choice_d = new frappe.ui.Dialog({
        title: __("How to pay commission to {0}?", [frm.doc.sales_partner]),
        fields: [
            {
                fieldname: "method",
                label: __("Payment Method"),
                fieldtype: "Select",
                options: "Additional Salary (Payroll)\nJournal Entry (Direct Bank Transfer)",
                default: "Additional Salary (Payroll)",
                reqd: 1,
                description: __(
                    "<b>Additional Salary:</b> Included in next payroll run. Recommended for employees.<br>"
                    + "<b>Journal Entry:</b> Direct bank payment. For bank transfers outside payroll."
                )
            }
        ],
        primary_action_label: __("Continue"),
        primary_action: function(vals) {
            choice_d.hide();
            if (vals.method === "Additional Salary (Payroll)") {
                _show_additional_salary_dialog(frm, info);
            } else {
                _show_je_dialog(frm);
            }
        }
    });
    choice_d.show();
}


// ── Main form events ───────────────────────────────────────────────────────

frappe.ui.form.on("Dlits Commission Management", {

    refresh: function(frm) {
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__("Calculate Commissions"), function() {
                frm.trigger("do_calculate");
            }).addClass("btn-primary");
        }

        frm.trigger("_update_group_ui");

        // ── Approval actions ────────────────────────────────────────────
        if (frm.doc.docstatus === 1 && frappe.user.has_role("Shb Commission Approver")) {

            if (frm.doc.status === "Requested for Approval" || frm.doc.status === "Approved") {
                frm.add_custom_button(__("Reject"), function() {
                    frappe.prompt(
                        [{ label: __("Rejection Reason"), fieldname: "reason", fieldtype: "Small Text", reqd: 1 }],
                        function(vals) {
                            frappe.call({
                                method: "dlitscustom.dlitscustom.doctype.dlits_commission_management.dlits_commission_management.reject_commission",
                                args: { name: frm.doc.name, rejection_reason: vals.reason },
                                callback: function(r) {
                                    if (!r.exc) {
                                        frm.reload_doc();
                                        frappe.show_alert({ message: __("Commission Rejected"), indicator: "red" });
                                    }
                                }
                            });
                        },
                        __("Reject Commission"), __("Reject")
                    );
                }, __("Actions")).addClass("btn-danger");
            }

            if (frm.doc.status === "Requested for Approval") {
                frm.add_custom_button(__("Approve"), function() {
                    frappe.confirm(
                        __("Approve commission for <b>{0}</b>?", [frm.doc.sales_partner]),
                        function() {
                            frappe.call({
                                method: "dlitscustom.dlitscustom.doctype.dlits_commission_management.dlits_commission_management.approve_commission",
                                args: { name: frm.doc.name },
                                callback: function(r) {
                                    if (!r.exc) {
                                        frm.reload_doc();
                                        frappe.show_alert({ message: __("Commission Approved"), indicator: "green" });
                                    }
                                }
                            });
                        }
                    );
                }, __("Actions")).addClass("btn-success");
            }
        }

        // ── Make Payment button ─────────────────────────────────────────
        if (frm.doc.docstatus === 1
                && frm.doc.status === "Approved"
                && flt(frm.doc.balance_commission) > 0
                && (frappe.user.has_role("Shb Commission Approver") || frappe.user.has_role("Accounts Manager"))) {
            frm.add_custom_button(__("Make Payment"), function() {
                frappe.call({
                    method: "dlitscustom.dlitscustom.doctype.dlits_commission_management.dlits_commission_management.get_partner_payment_info",
                    args: { sales_partner: frm.doc.sales_partner },
                    callback: function(r) {
                        if (r.exc) return;
                        const info = r.message || {};
                        if (info.partner_type === "Internal User" && info.employee) {
                            _show_payment_method_choice(frm, info);
                        } else {
                            _show_je_dialog(frm);
                        }
                    }
                });
            }, __("Actions")).addClass("btn-primary");
        }
    },

    sales_partner: function(frm) {
        if (!frm.doc.sales_partner) {
            frm.set_value("is_group_partner", 0);
            frm.trigger("_update_group_ui");
            return;
        }
        frappe.db.get_value(
            "Dlits Sales Partner",
            frm.doc.sales_partner,
            ["commission_rate", "is_group"],
            function(r) {
                if (!r) return;
                if (r.commission_rate) frm.set_value("commission_rate", r.commission_rate);
                frm.set_value("is_group_partner", r.is_group ? 1 : 0);
                frm.trigger("_update_group_ui");
            }
        );
    },

    _update_group_ui: function(frm) {
        if (frm.doc.is_group_partner) {
            let sec = frm.get_field("section_filters");
            if (sec && sec.df) { sec.df.collapsible = 0; sec.df.collapsed = 0; }
            frm.refresh_field("section_filters");
            frm.set_df_property("cost_center", "bold", 1);
        } else {
            frm.set_df_property("section_filters", "collapsible", 1);
            frm.set_df_property("cost_center", "bold", 0);
            frm.refresh_field("section_filters");
        }
    },

    do_calculate: function(frm) {
        if (!frm.doc.sales_partner || !frm.doc.from_date || !frm.doc.to_date || !frm.doc.commission_rate) {
            frappe.msgprint(__("Please fill Sales Partner, From Date, To Date and Commission Rate first."));
            return;
        }
        if (frm.doc.is_group_partner && !frm.doc.cost_center) {
            frappe.msgprint(__("Cost Center is mandatory for Group commission calculation."));
            return;
        }

        frappe.call({
            method: "dlitscustom.dlitscustom.doctype.dlits_commission_management.dlits_commission_management.get_commission_invoices",
            args: {
                sales_partner:            frm.doc.sales_partner,
                from_date:                frm.doc.from_date,
                to_date:                  frm.doc.to_date,
                commission_rate:          frm.doc.commission_rate,
                cost_center:              frm.doc.cost_center || null,
                brand:                    frm.doc.brand || null,
                item:                     frm.doc.item || null,
                exclude_unpaid_invoices:  frm.doc.exclude_unpaid_invoices  ? 1 : 0,
                exclude_partial_invoices: frm.doc.exclude_partial_invoices ? 1 : 0,
                exclude_unpaid_returns:   frm.doc.exclude_unpaid_returns   ? 1 : 0,
                exclude_partial_returns:  frm.doc.exclude_partial_returns  ? 1 : 0,
                service_cost_percentage:  frm.doc.service_cost_percentage || 75,
                current_doc:              frm.doc.__islocal ? null : frm.doc.name
            },
            freeze: true,
            freeze_message: __("Fetching invoices..."),
            callback: function(r) {
                if (r.exc) return;
                frm.clear_table("invoices");
                (r.message || []).forEach(function(inv) {
                    let row = frm.add_child("invoices");
                    row.sales_invoice      = inv.sales_invoice;
                    row.is_return          = inv.is_return ? 1 : 0;
                    row.posting_date       = inv.posting_date;
                    row.customer           = inv.customer;
                    row.net_total          = inv.net_total;
                    row.grand_total        = inv.grand_total;
                    row.tax_amount         = inv.tax_amount;
                    row.paid_amount        = inv.paid_amount;
                    row.outstanding_amount = inv.outstanding_amount;
                    row.profit             = inv.profit;
                    row.commission_amount  = inv.commission_amount;
                    row.is_marked          = 0;
                    row.is_gp_marked       = 0;
                });
                frm.refresh_field("invoices");
                frm.trigger("recalculate_totals");
                frm.set_value("status", "Calculated");

                let regular = (r.message || []).filter(i => !i.is_return).length;
                let returns  = (r.message || []).filter(i =>  i.is_return).length;
                if (!r.message || r.message.length === 0) {
                    frappe.msgprint(__("No invoices found for the selected criteria."));
                } else {
                    frappe.show_alert({
                        message: __("{0} invoice(s) + {1} return(s) fetched.", [regular, returns]),
                        indicator: "green"
                    });
                }
            }
        });
    },

    recalculate_totals: function(frm) {
        let total_net = 0, total_gross = 0, total_profit = 0, total_commission = 0;
        (frm.doc.invoices || []).forEach(function(row) {
            total_net        += flt(row.net_total);
            total_gross      += flt(row.grand_total);
            total_profit     += flt(row.profit);
            total_commission += flt(row.commission_amount);
        });
        frm.set_value("total_net_amount",   total_net);
        frm.set_value("total_gross_amount", total_gross);
        frm.set_value("total_profit",       total_profit);
        frm.set_value("total_commission",   total_commission);

        let total_paid = 0;
        (frm.doc.payments || []).forEach(function(row) { total_paid += flt(row.amount); });
        frm.set_value("total_paid",         total_paid);
        frm.set_value("balance_commission", total_commission - total_paid);
    }
});

frappe.ui.form.on("Dlits Commission Invoice", {
    profit:           function(frm) { frm.trigger("recalculate_totals"); },
    commission_amount:function(frm) { frm.trigger("recalculate_totals"); },
    invoices_remove:  function(frm) { frm.trigger("recalculate_totals"); }
});

frappe.ui.form.on("Dlits Commission Payment", {

    reference_type: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const doctype_map = {
            "Additional Salary": "Additional Salary",
            "Journal Entry":     "Journal Entry",
            "Payment Entry":     "Payment Entry",
        };
        const doctype = doctype_map[row.reference_type] || "";
        frappe.model.set_value(cdt, cdn, "reference_doctype", doctype);
        frappe.model.set_value(cdt, cdn, "reference_name",    "");
        frappe.model.set_value(cdt, cdn, "payment_date",      "");
        frappe.model.set_value(cdt, cdn, "amount",            0);
        frm.set_query("reference_name", "payments", function() {
            return { filters: { docstatus: 1 } };
        });
    },

    reference_name: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.reference_name || !row.reference_type) return;

        if (row.reference_type === "Additional Salary") {
            frappe.db.get_value("Additional Salary", row.reference_name,
                ["payroll_date", "amount"], function(r) {
                    if (!r) return;
                    frappe.model.set_value(cdt, cdn, "payment_date", r.payroll_date);
                    frappe.model.set_value(cdt, cdn, "amount",       r.amount);
                    frm.trigger("recalculate_totals");
                }
            );
        } else if (row.reference_type === "Journal Entry") {
            frappe.db.get_value("Journal Entry", row.reference_name,
                ["posting_date", "total_debit"], function(r) {
                    if (!r) return;
                    frappe.model.set_value(cdt, cdn, "payment_date", r.posting_date);
                    frappe.model.set_value(cdt, cdn, "amount",       r.total_debit);
                    frm.trigger("recalculate_totals");
                }
            );
        } else if (row.reference_type === "Payment Entry") {
            frappe.db.get_value("Payment Entry", row.reference_name,
                ["posting_date", "paid_amount"], function(r) {
                    if (!r) return;
                    frappe.model.set_value(cdt, cdn, "payment_date", r.posting_date);
                    frappe.model.set_value(cdt, cdn, "amount",       r.paid_amount);
                    frm.trigger("recalculate_totals");
                }
            );
        }
    },

    amount:          function(frm) { frm.trigger("recalculate_totals"); },
    payments_remove: function(frm) { frm.trigger("recalculate_totals"); }
});
