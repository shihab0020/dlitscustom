// Helper to always fetch the customer using the parent customer_name
async function get_customer(frm) {
  if (frm.doc.customer_name) {
    let r = await frappe.db.get_value("Customer", { customer_name: frm.doc.customer_name }, "name");
    if (r && r.message && r.message.name) {
      return r.message.name;
    }
  }
  // fallback if customer_name isn’t set
  return frm.doc.customer;
}

// Helper to get price list robustly
function get_price_list(frm) {
  return frm.doc.price_list || frm.doc.selling_price_list;
}

// Central function applying our custom pricing rule.
// We wrap our rate updates with a temporary flag (_suppress_manual_rate) so that
// the "rate" event handler can later tell that these updates were automatic.
async function apply_pricing_rule(frm, cdt, cdn) {
  let row = locals[cdt][cdn];

  if (row.prevdoc_docname || row.prevdoc_detail_docname) {
    console.log("[PricingRule] Skipping row linked to a source document.");
    return;
  }

  let customer = await get_customer(frm);
  let price_list = get_price_list(frm);
  if (!row.item_code || !customer || !price_list) return;

  // Respect existing manual override if set
  if (row.custom_manual_rate) {
    console.log("[PricingRule] Manual rate present. Not reapplying auto pricing rule.");
    return;
  }

  frappe.call({
    method: "dlitscustom.utils.get_pricing_rule_dlits.get_pricing_rule_dlits",
    args: {
      item_code: row.item_code,
      customer: customer,
      price_list: price_list
    },
    callback: function(r) {
      if (r.message) {
        // Mark that this update is auto‐driven.
        row._suppress_manual_rate = true;
        frappe.model.set_value(cdt, cdn, 'rate', r.message);
        frappe.model.set_value(cdt, cdn, 'price_list_rate', r.message);
        // Clear any stored manual override data
        frappe.model.set_value(cdt, cdn, 'custom_manual_rate', 0);
        frappe.model.set_value(cdt, cdn, 'custom_user_set_rate', '');
        console.log("[PricingRule] Applied pricing rule rate: " + r.message);
        // Remove the suppression flag after a short delay so subsequent user edits will be detected.
        setTimeout(function() {
          row._suppress_manual_rate = false;
        }, 100);
      }
    }
  });
}

// Event handlers on Sales Order Item
frappe.ui.form.on('Sales Order Item', {
  // When a new item is added or the item code is changed,
  // clear previous manual flags and then reapply our pricing rule.
  item_code: function(frm, cdt, cdn) {
    frappe.model.set_value(cdt, cdn, 'custom_manual_rate', 0);
    frappe.model.set_value(cdt, cdn, 'custom_user_set_rate', '');
    setTimeout(function() {
      apply_pricing_rule(frm, cdt, cdn);
    }, 300);
  },

  // On qty change, reapply pricing rule only if the user hasn’t already set a manual rate.
  qty: function(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (!row.custom_manual_rate) {
      setTimeout(function() {
        apply_pricing_rule(frm, cdt, cdn);
      }, 300);
    }
  },

  // On UOM change, again reapply if no manual override is in place.
  uom: function(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (!row.custom_manual_rate) {
      setTimeout(function() {
        apply_pricing_rule(frm, cdt, cdn);
      }, 300);
    }
  },

  // The rate event handler: only mark a manual override when the user manually changes the rate.
  // We do this by checking two things:
  // 1. If our temporary auto-update flag (_suppress_manual_rate) is set, that means the change came from our code.
  // 2. Whether the field is actively being edited by the user (i.e. the input is currently focused).
  rate: function(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    // If this update was triggered automatically, do nothing.
    if (row._suppress_manual_rate) {
      console.log("[PricingRule] Auto update; not marking manual override.");
      return;
    }
    // Check if the active element is the rate input field.
    let active = document.activeElement;
    if (active && $(active).attr("data-fieldname") === "rate") {
      // Mark the row as manually overridden.
      frappe.model.set_value(cdt, cdn, 'custom_manual_rate', 1);
      frappe.model.set_value(cdt, cdn, 'custom_user_set_rate', row.rate);
      console.log("[PricingRule] Manual override detected via input activity, new rate: " + row.rate);
    } else {
      // Likely a non-user update (from ERPNext default backend logic); do not mark as manual.
      console.log("[PricingRule] Rate event not triggered by active user editing; ignoring.");
    }
  }
});

// Bind form-level events on Sales Order so that dependent changes (like customer or price_list)
// reapply our pricing rule on all items (unless a manual override already exists)
frappe.ui.form.on('Sales Order', {
  customer: function(frm) {
    if (frm.doc.items) {
      frm.doc.items.forEach(function(row) {
        if (!row.custom_manual_rate) {
          setTimeout(function() {
            apply_pricing_rule(frm, row.doctype, row.name);
          }, 300);
        }
      });
    }
  },
  price_list: function(frm) {
    if (frm.doc.items) {
      frm.doc.items.forEach(function(row) {
        if (!row.custom_manual_rate) {
          setTimeout(function() {
            apply_pricing_rule(frm, row.doctype, row.name);
          }, 300);
        }
      });
    }
  }
});
