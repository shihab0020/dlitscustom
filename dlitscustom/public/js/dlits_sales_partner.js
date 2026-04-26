frappe.ui.form.on("Dlits Sales Partner", {
    setup: function(frm) {
        frm.set_query("sales_partner", "group_members", function() {
            return {
                filters: {
                    is_group: 0,
                    status: "Active"
                }
            };
        });
    },

    is_group: function(frm) {
        if (frm.doc.is_group) {
            frm.set_value("partner_type", "");
            frm.set_value("user", "");
        } else {
            frm.set_value("partner_type", "Internal User");
        }
    }
});
