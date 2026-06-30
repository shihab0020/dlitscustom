frappe.ui.form.on("Sales Invoice", {

    refresh: function(frm) {
        // Show commission button only on submitted invoices that have a fixed commission
        if (frm.doc.docstatus !== 1 || frm.doc.is_return) return;

        if (frm.doc.dlits_commission_ref) {
            frm.add_custom_button("View Invoice Commission", function() {
                frappe.set_route("Form", "Dlits Invoice Commission", frm.doc.dlits_commission_ref);
            }).addClass("btn-primary");
        } else if (flt(frm.doc.dlits_fixed_commission) > 0
                   && (frappe.user.has_role("Shb Commission Approver") || frappe.user.has_role("Accounts Manager"))) {
            frm.add_custom_button("Create Commission Record", function() {
                frappe.confirm(
                    "Commission record not found. Create one now?",
                    function() {
                        frappe.call({
                            method: "dlitscustom.override.invoice_commission_events.create_commission_from_form",
                            args: { sales_invoice: frm.doc.name },
                            callback: function(r) {
                                if (r.message) {
                                    frm.reload_doc();
                                    frappe.show_alert({ message: "Commission record created.", indicator: "green" });
                                }
                            }
                        });
                    }
                );
            });
        }
    },

    dlits_is_me: function(frm) {
        if (!frm.doc.dlits_is_me) return;

        frappe.call({
            method: "dlitscustom.dlitscustom.doctype.dlits_sales_partner.dlits_sales_partner.get_partner_by_user",
            callback: function(r) {
                if (r.message && r.message.name) {
                    frm.set_value("dlits_sales_partner", r.message.name);
                } else {
                    frappe.show_alert({
                        message: __("No active Dlits Sales Partner linked to your user account."),
                        indicator: "orange"
                    });
                    frm.set_value("dlits_is_me", 0);
                }
            }
        });
    },

    dlits_sales_partner: function(frm) {
        // Clear the Me checkbox if the partner is changed manually
        if (frm.doc.dlits_is_me && !frm.doc.dlits_sales_partner) {
            frm.set_value("dlits_is_me", 0);
        }
    }
});
