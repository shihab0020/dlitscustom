frappe.ui.form.on("Dlits Sales Partner", {

    setup: function(frm) {
        frm.set_query("sales_partner", "group_members", function() {
            return {
                filters: { is_group: 0, status: "Active" }
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
    },

    partner_type: function(frm) {
        frm.toggle_reqd("user", frm.doc.partner_type === "Internal User");
    },

    user: function(frm) {
        if (frm.doc.partner_type === "Internal User" && frm.doc.user && !frm.doc.partner_name) {
            frappe.db.get_value("User", frm.doc.user, "full_name", function(r) {
                if (r && r.full_name) frm.set_value("partner_name", r.full_name);
            });
        }
    }
});
