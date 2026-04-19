import frappe
from frappe.model.document import Document


class DlitsSalesPartner(Document):
    def before_save(self):
        if self.partner_type == "Internal User" and self.user and not self.partner_name:
            user_doc = frappe.get_doc("User", self.user)
            self.partner_name = user_doc.full_name or self.user


@frappe.whitelist()
def get_partner_by_user(user=None):
    """Return the active Dlits Sales Partner linked to the given user (defaults to session user)."""
    if not user:
        user = frappe.session.user
    partner = frappe.db.get_value(
        "Dlits Sales Partner",
        {"user": user, "partner_type": "Internal User", "status": "Active"},
        ["name", "partner_name"],
        as_dict=True
    )
    return partner
