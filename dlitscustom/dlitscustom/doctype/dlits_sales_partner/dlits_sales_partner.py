import frappe
from frappe.model.document import Document


class DlitsSalesPartner(Document):
    def before_save(self):
        if self.partner_type == "Internal User" and self.user and not self.partner_name:
            user_doc = frappe.get_doc("User", self.user)
            self.partner_name = user_doc.full_name or self.user


@frappe.whitelist()
def get_partner_by_user(user=None):
    """Return the active Dlits Sales Partner for the session user.

    If the user's individual partner belongs to a group, the group is returned
    so commission invoices are attributed to the group, not the individual.
    """
    if not user:
        user = frappe.session.user

    individual = frappe.db.get_value(
        "Dlits Sales Partner",
        {"user": user, "partner_type": "Internal User", "status": "Active", "is_group": 0},
        "name"
    )
    if not individual:
        return None

    # Check if this individual is a member of any active group
    group_name = frappe.db.get_value(
        "Dlits Sales Partner Member",
        {"sales_partner": individual, "parenttype": "Dlits Sales Partner"},
        "parent"
    )

    target = group_name if group_name else individual
    return frappe.db.get_value("Dlits Sales Partner", target, ["name", "partner_name"], as_dict=True)
