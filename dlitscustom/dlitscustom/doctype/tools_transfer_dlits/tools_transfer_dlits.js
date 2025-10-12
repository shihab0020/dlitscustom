// Copyright (c) 2024, DLITS and contributors
// For license information, please see license.txt

frappe.ui.form.on('Tools Transfer Dlits', {
	refresh: function(frm) {
		// Add custom buttons
		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('View Stock Entry'), function() {
				if (frm.doc.stock_entry) {
					frappe.set_route('Form', 'Stock Entry', frm.doc.stock_entry);
				} else {
					frappe.msgprint(__('No Stock Entry linked to this transfer'));
				}
			});
		}
		
		// Set color indicators for status
		if (frm.doc.status === 'Completed') {
			frm.dashboard.set_headline_alert(__('Transfer Completed'), 'green');
		} else if (frm.doc.status === 'Cancelled') {
			frm.dashboard.set_headline_alert(__('Transfer Cancelled'), 'red');
		}
	},
	
	source_type: function(frm) {
		// Clear source fields when type changes
		frm.set_value('source_warehouse', '');
		frm.set_value('source_employee', '');
		
		// Set warehouse filter
		if (frm.doc.source_type === 'Warehouse') {
			set_warehouse_filter(frm, 'source_warehouse');
		}
	},
	
	to_type: function(frm) {
		// Clear destination fields when type changes
		frm.set_value('to_warehouse', '');
		frm.set_value('to_employee', '');
		
		// Set warehouse filter
		if (frm.doc.to_type === 'Warehouse') {
			set_warehouse_filter(frm, 'to_warehouse');
		}
	},
	
	company: function(frm) {
		// Clear warehouse fields when company changes
		frm.set_value('source_warehouse', '');
		frm.set_value('to_warehouse', '');
		
		// Update warehouse filters
		if (frm.doc.source_type === 'Warehouse') {
			set_warehouse_filter(frm, 'source_warehouse');
		}
		if (frm.doc.to_type === 'Warehouse') {
			set_warehouse_filter(frm, 'to_warehouse');
		}
	},
	
	item: function(frm) {
		// Check stock availability when item is selected
		if (frm.doc.item && frm.doc.source_type === 'Warehouse' && frm.doc.source_warehouse) {
			check_stock_availability(frm);
		}
	},
	
	source_warehouse: function(frm) {
		// Check stock availability when source warehouse is selected
		if (frm.doc.item && frm.doc.source_warehouse) {
			check_stock_availability(frm);
		}
	},
	
	qty: function(frm) {
		// Check stock availability when quantity changes
		if (frm.doc.item && frm.doc.source_type === 'Warehouse' && frm.doc.source_warehouse) {
			check_stock_availability(frm);
		}
	},
	
	allow_negative_stock: function(frm) {
		if (frm.doc.allow_negative_stock) {
			frappe.msgprint({
				title: __('Negative Stock Allowed'),
				message: __('You have enabled negative stock transfers. Please ensure this is intentional as it may affect inventory accuracy.'),
				indicator: 'orange'
			});
		}
	}
});

function check_stock_availability(frm) {
	if (!frm.doc.item || !frm.doc.source_warehouse || !frm.doc.qty) {
		return;
	}
	
	frappe.call({
		method: 'frappe.client.get_value',
		args: {
			doctype: 'Bin',
			filters: {
				item_code: frm.doc.item,
				warehouse: frm.doc.source_warehouse
			},
			fieldname: 'actual_qty'
		},
		callback: function(r) {
			if (r.message) {
				let available_qty = r.message.actual_qty || 0;
				let required_qty = frm.doc.qty || 0;
				
				if (required_qty > available_qty) {
					// Show warning and suggest enabling negative stock
					frm.dashboard.clear_headline();
					frm.dashboard.set_headline_alert(
						__('Insufficient Stock: Available {0}, Required {1}', [available_qty, required_qty]), 
						'orange'
					);
					
					if (!frm.doc.allow_negative_stock) {
						frappe.msgprint({
							title: __('Insufficient Stock'),
							message: __('Available quantity ({0}) is less than required ({1}). You can check "Allow Negative Stock" to proceed with this transfer.', [available_qty, required_qty]),
							indicator: 'orange'
						});
					}
				} else {
					frm.dashboard.clear_headline();
					frm.dashboard.set_headline_alert(
						__('Stock Available: {0}', [available_qty]), 
						'green'
					);
				}
			}
		}
	});
}

function set_warehouse_filter(frm, fieldname) {
	if (frm.doc.company) {
		frm.set_query(fieldname, function() {
			return {
				filters: {
					company: frm.doc.company
				}
			};
		});
	}
}