frappe.ui.form.on("Dlits Sales Partner", {
    partner_type: function(frm) {
        frm.toggle_reqd("user", frm.doc.partner_type === "Internal User");
    },

    user: function(frm) {
        if (frm.doc.partner_type === "Internal User" && frm.doc.user && !frm.doc.partner_name) {
            frappe.db.get_value("User", frm.doc.user, "full_name", function(r) {
                if (r && r.full_name) {
                    frm.set_value("partner_name", r.full_name);
                }
            });
        }
    }
});
