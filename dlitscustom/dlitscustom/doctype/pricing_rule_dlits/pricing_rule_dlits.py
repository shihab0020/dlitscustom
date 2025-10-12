import frappe
from frappe.model.document import Document
from frappe import _

class PricingRuleDlits(Document):
    """Custom Pricing Rule DocType for DLITS"""
    
    def validate(self):
        self.validate_item_rate_settings()
        self.validate_apply_on_restrictions()
        self.validate_discount_fields()
    
    def validate_item_rate_settings(self):
        """Validate settings when base_price_type is 'Item Rate'"""
        if self.base_price_type == 'Item Rate':
            # Ensure Apply On is set to Item Code
            if self.apply_on != 'Item Code':
                frappe.throw(_("Apply On must be 'Item Code' when Base Price Type is 'Item Rate'"))
            
            # Ensure at least one item is specified
            if not self.items:
                frappe.throw(_("At least one item must be specified when Base Price Type is 'Item Rate'"))
            
            # Validate that price_value is set for all items
            for item in self.items:
                if not item.price_value or item.price_value <= 0:
                    frappe.throw(_("Price Value must be set and greater than 0 for item {0} when Base Price Type is 'Item Rate'").format(item.item_code))
    
    def validate_apply_on_restrictions(self):
        """Validate that required fields are set based on apply_on selection"""
        if self.base_price_type != 'Item Rate':
            # Normal validation for margin/discount based pricing
            if self.apply_on == 'Item Code' and not self.items:
                frappe.throw(_("At least one item must be specified when Apply On is 'Item Code'"))
            elif self.apply_on == 'Item Group' and not self.item_groups:
                frappe.throw(_("At least one item group must be specified when Apply On is 'Item Group'"))
            elif self.apply_on == 'Brand' and not self.brands:
                frappe.throw(_("At least one brand must be specified when Apply On is 'Brand'"))
        else:
            # For Item Rate, only Item Code is allowed
            if self.apply_on == 'Item Code' and not self.items:
                frappe.throw(_("At least one item must be specified when Base Price Type is 'Item Rate'"))
    
    def validate_discount_fields(self):
        """Skip discount/margin field validation when base_price_type is 'Item Rate'"""
        if self.base_price_type == 'Item Rate':
            # Clear discount fields when Item Rate is selected to avoid validation errors
            self.discount_type = None
            self.discount_value = None
        else:
            # For other base price types, ensure discount fields are set
            if not self.discount_type:
                frappe.throw(_("Type (Margin or Discount) is required when Base Price Type is not 'Item Rate'"))
            if self.discount_value is None or self.discount_value == 0:
                frappe.throw(_("Value (Margin or Discount) is required when Base Price Type is not 'Item Rate'"))
