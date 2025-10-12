frappe.ui.form.on('Pricing Rule Dlits', {
    refresh: function(frm) {
        frm.trigger('base_price_type');
        frm.trigger('apply_on');
    },
    
    base_price_type: function(frm) {
        // Handle different base price types
        let help = '';
        let options = [];
        
        if (frm.doc.base_price_type === 'Item Rate') {
            // When Item Rate is selected
            help = 'Item Rate: Set direct price values for each item in the child table.';
            
            // Set Apply On to Item Code and make it read-only
            frm.set_value('apply_on', 'Item Code');
            frm.set_df_property('apply_on', 'read_only', 1);
            
            // Hide discount type and value fields
            frm.set_df_property('discount_type', 'hidden', 1);
            frm.set_df_property('discount_value', 'hidden', 1);
            frm.set_df_property('discount_type', 'reqd', 0);
            frm.set_df_property('discount_value', 'reqd', 0);
            
            // Show only items table
            frm.set_df_property('items', 'hidden', 0);
            frm.set_df_property('item_groups', 'hidden', 1);
            frm.set_df_property('brands', 'hidden', 1);
            
        } else {
            // For other base price types (Price List Rate, Valuation Rate, Selling Rate)
            // Make Apply On editable again
            frm.set_df_property('apply_on', 'read_only', 0);
            
            // Show discount type and value fields
            frm.set_df_property('discount_type', 'hidden', 0);
            frm.set_df_property('discount_value', 'hidden', 0);
            frm.set_df_property('discount_type', 'reqd', 1);
            frm.set_df_property('discount_value', 'reqd', 1);
            
            // Set appropriate options and help text
            if (frm.doc.base_price_type === 'Valuation Rate') {
                help = 'Valuation Rate: Uses item master valuation rate with applied margin.';
                options = ['Rate (Percentage)', 'Margin Amount'];
            } else if (frm.doc.base_price_type === 'Selling Rate') {
                help = 'Selling Rate: Uses item master standard selling rate with applied discount.';
                options = ['Discount Percentage', 'Discount Amount'];
            } else if (frm.doc.base_price_type === 'Price List Rate') {
                help = 'Price List Rate: Uses ERPNext price list rate with applied discount.';
                options = ['Discount Percentage', 'Discount Amount'];
            }
            
            frm.set_df_property('discount_type', 'options', options.join('\n'));
            
            // Show/hide tables based on apply_on value
            frm.trigger('apply_on');
        }
        
        frm.set_df_property('base_price_type', 'description', help);
        
        // Refresh the child table to show/hide price_value field
        if (frm.doc.items) {
            frm.refresh_field('items');
        }
        
        // Update discount_value label/help if not Item Rate
        if (frm.doc.base_price_type !== 'Item Rate') {
            frm.trigger('discount_type');
        }
    },
    
    apply_on: function(frm) {
        // Only handle apply_on changes when base_price_type is not Item Rate
        if (frm.doc.base_price_type !== 'Item Rate') {
            // Show/hide appropriate tables based on apply_on selection
            frm.set_df_property('items', 'hidden', frm.doc.apply_on !== 'Item Code');
            frm.set_df_property('item_groups', 'hidden', frm.doc.apply_on !== 'Item Group');
            frm.set_df_property('brands', 'hidden', frm.doc.apply_on !== 'Brand');
        }
    },
    discount_type: function(frm) {
        // Dynamic label and help for discount_value based on base_price_type
        let label = 'Value (Margin or Discount)';
        let help = '';
        
        if (frm.doc.base_price_type === 'Valuation Rate') {
            if (frm.doc.discount_type === 'Rate (Percentage)') {
                label = 'Margin Percentage';
                help = 'Adds margin percentage to valuation rate.';
            } else if (frm.doc.discount_type === 'Margin Amount') {
                label = 'Margin Amount';
                help = 'Adds fixed margin amount to valuation rate.';
            } else {
                label = 'Margin';
                help = 'Margin is added to valuation rate.';
            }
        } else {
            if (frm.doc.discount_type === 'Rate (Percentage)' || frm.doc.discount_type === 'Discount Percentage') {
                label = 'Discount Percentage';
                help = 'Discount percentage is subtracted from base rate.';
            } else if (frm.doc.discount_type === 'Discount Amount') {
                label = 'Discount Amount';
                help = 'Discount amount is subtracted from base rate.';
            } else if (frm.doc.discount_type === 'Margin Amount') {
                label = 'Margin Amount';
                help = 'Margin amount is added to base rate.';
            } else {
                label = 'Value';
                help = 'Value to be applied to base rate.';
            }
        }
        
        frm.fields_dict.discount_value.df.label = label;
        frm.fields_dict.discount_value.df.description = help;
        frm.refresh_field('discount_value');
    }
});


