frappe.ui.form.on("Dlits Commission Management", {

    refresh: function(frm) {
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__("Calculate Commissions"), function() {
                frm.trigger("do_calculate");
            }).addClass("btn-primary");
        }
        frm.trigger("_update_group_ui");
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
            if (sec && sec.df) {
                sec.df.collapsible = 0;
                sec.df.collapsed   = 0;
            }
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
        (frm.doc.payments || []).forEach(function(row) {
            total_paid += flt(row.amount);
        });
        frm.set_value("total_paid",         total_paid);
        frm.set_value("balance_commission", total_commission - total_paid);
    }
});

frappe.ui.form.on("Dlits Commission Invoice", {
    profit: function(frm)            { frm.trigger("recalculate_totals"); },
    commission_amount: function(frm) { frm.trigger("recalculate_totals"); },
    invoices_remove: function(frm)   { frm.trigger("recalculate_totals"); }
});

frappe.ui.form.on("Dlits Commission Payment", {

    reference_type: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const doctype_map = {
            "Payment Entry":     "Payment Entry",
            "Credit Note":       "Sales Invoice",
            "Additional Salary": "Additional Salary"
        };
        const doctype = doctype_map[row.reference_type] || "";
        frappe.model.set_value(cdt, cdn, "reference_doctype", doctype);
        frappe.model.set_value(cdt, cdn, "reference_name", "");
        frappe.model.set_value(cdt, cdn, "payment_date", "");
        frappe.model.set_value(cdt, cdn, "amount", 0);

        // For Credit Note: filter to return invoices only
        if (row.reference_type === "Credit Note") {
            frm.set_query("reference_name", "payments", function() {
                return { filters: { is_return: 1, docstatus: 1 } };
            });
        } else if (row.reference_type === "Payment Entry") {
            frm.set_query("reference_name", "payments", function() {
                return { filters: { docstatus: 1 } };
            });
        } else if (row.reference_type === "Additional Salary") {
            frm.set_query("reference_name", "payments", function() {
                return { filters: { docstatus: 1 } };
            });
        } else {
            frm.set_query("reference_name", "payments", function() { return {}; });
        }
    },

    reference_name: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.reference_name || !row.reference_type) return;

        if (row.reference_type === "Payment Entry") {
            frappe.db.get_value("Payment Entry", row.reference_name,
                ["posting_date", "paid_amount"],
                function(r) {
                    if (!r) return;
                    frappe.model.set_value(cdt, cdn, "payment_date", r.posting_date);
                    frappe.model.set_value(cdt, cdn, "amount", r.paid_amount);
                    frm.trigger("recalculate_totals");
                }
            );
        } else if (row.reference_type === "Credit Note") {
            frappe.db.get_value("Sales Invoice", row.reference_name,
                ["posting_date", "grand_total"],
                function(r) {
                    if (!r) return;
                    frappe.model.set_value(cdt, cdn, "payment_date", r.posting_date);
                    // Credit note grand_total is negative; store as positive amount
                    frappe.model.set_value(cdt, cdn, "amount", Math.abs(r.grand_total));
                    frm.trigger("recalculate_totals");
                }
            );
        } else if (row.reference_type === "Additional Salary") {
            frappe.db.get_value("Additional Salary", row.reference_name,
                ["payroll_date", "amount"],
                function(r) {
                    if (!r) return;
                    frappe.model.set_value(cdt, cdn, "payment_date", r.payroll_date);
                    frappe.model.set_value(cdt, cdn, "amount", r.amount);
                    frm.trigger("recalculate_totals");
                }
            );
        }
    },

    amount: function(frm) { frm.trigger("recalculate_totals"); },
    payments_remove: function(frm) { frm.trigger("recalculate_totals"); }
});
