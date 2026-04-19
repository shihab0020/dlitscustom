frappe.ui.form.on("Sales Invoice", {

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
