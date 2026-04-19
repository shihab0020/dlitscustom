frappe.ui.form.on("Dlits Commission Management", {

    refresh: function(frm) {
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__("Calculate Commissions"), function() {
                frm.trigger("do_calculate");
            }).addClass("btn-primary");
        }
    },

    sales_partner: function(frm) {
        if (frm.doc.sales_partner) {
            frappe.db.get_value("Dlits Sales Partner", frm.doc.sales_partner, "commission_rate", function(r) {
                if (r && r.commission_rate) {
                    frm.set_value("commission_rate", r.commission_rate);
                }
            });
        }
    },

    do_calculate: function(frm) {
        if (!frm.doc.sales_partner || !frm.doc.from_date || !frm.doc.to_date || !frm.doc.commission_rate) {
            frappe.msgprint(__("Please fill Sales Partner, From Date, To Date and Commission Rate first."));
            return;
        }

        frappe.call({
            method: "dlitscustom.dlitscustom.doctype.dlits_commission_management.dlits_commission_management.get_commission_invoices",
            args: {
                sales_partner: frm.doc.sales_partner,
                from_date: frm.doc.from_date,
                to_date: frm.doc.to_date,
                commission_rate: frm.doc.commission_rate,
                cost_center: frm.doc.cost_center || null,
                brand: frm.doc.brand || null,
                item: frm.doc.item || null,
                avoid_draft_invoices: frm.doc.avoid_draft_invoices ? 1 : 0,
                avoid_non_paid_invoices: frm.doc.avoid_non_paid_invoices ? 1 : 0,
                avoid_partial_paid: frm.doc.avoid_partial_paid ? 1 : 0,
                deduct_return: frm.doc.deduct_return ? 1 : 0,
                service_cost_percentage: frm.doc.service_cost_percentage || 75
            },
            freeze: true,
            freeze_message: __("Fetching invoices..."),
            callback: function(r) {
                if (r.exc) return;

                frm.clear_table("invoices");

                (r.message || []).forEach(function(inv) {
                    let row = frm.add_child("invoices");
                    row.sales_invoice      = inv.sales_invoice;
                    row.posting_date       = inv.posting_date;
                    row.customer           = inv.customer;
                    row.net_total          = inv.net_total;
                    row.grand_total        = inv.grand_total;
                    row.tax_amount         = inv.tax_amount;
                    row.paid_amount        = inv.paid_amount;
                    row.outstanding_amount = inv.outstanding_amount;
                    row.return_amount      = inv.return_amount || 0;
                    row.profit             = inv.profit;
                    row.commission_amount  = inv.commission_amount;
                    row.is_marked          = 0;
                });

                frm.refresh_field("invoices");
                frm.trigger("recalculate_totals");
                frm.set_value("status", "Calculated");

                if (!r.message || r.message.length === 0) {
                    frappe.msgprint(__("No invoices found for the selected criteria."));
                } else {
                    frappe.show_alert({
                        message: __("{0} invoice(s) fetched.", [r.message.length]),
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
    payment_entry: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.payment_entry) return;
        frappe.db.get_value("Payment Entry", row.payment_entry,
            ["posting_date", "payment_type", "paid_amount"],
            function(r) {
                if (!r) return;
                frappe.model.set_value(cdt, cdn, "payment_date", r.posting_date);
                frappe.model.set_value(cdt, cdn, "payment_type", r.payment_type);
                frappe.model.set_value(cdt, cdn, "amount", r.paid_amount);
                frm.trigger("recalculate_totals");
            }
        );
    },
    payments_remove: function(frm) { frm.trigger("recalculate_totals"); }
});
