// ── Dlits Margin — Sales Order ────────────────────────────────────────────────
// On save: Python validate hook (margin_sync.py) writes correct data to DB.
// On refresh of a SAVED doc: only render the summary — do NOT re-sync the table,
//   because clear_table + add_child would dirty the form and hide the Submit button.
// On refresh of a NEW doc: sync from items (nothing saved yet).
// On item edits: always full sync (form is already dirty from the user's edits).

frappe.ui.form.on('Sales Order', {
    onload(frm)  { _so_on_refresh(frm); },
    refresh(frm) { _so_on_refresh(frm); },
    items_remove(frm) { _so_schedule_sync(frm); },
    discount_amount(frm)               { _dlits_render_summary(frm); },
    additional_discount_percentage(frm){ _dlits_render_summary(frm); },
    apply_discount_on(frm)             { _dlits_render_summary(frm); },
});

frappe.ui.form.on('Sales Order Item', {
    item_code(frm) { _so_schedule_sync(frm); },
    qty(frm)       { _so_schedule_sync(frm); },
    rate(frm)      { _so_schedule_sync(frm); },
});

// Guard: only fire for Sales Order parent
frappe.ui.form.on('Dlits Margin Table Item', {
    cost(frm, cdt, cdn) {
        if (frm.doctype === 'Sales Order') _dlits_recalc_row(frm, cdt, cdn);
    },
    discount_type(frm, cdt, cdn) {
        if (frm.doctype === 'Sales Order') _dlits_recalc_row(frm, cdt, cdn);
    },
    discount(frm, cdt, cdn) {
        if (frm.doctype === 'Sales Order') _dlits_recalc_row(frm, cdt, cdn);
    },
});

let _so_margin_timer = null;

function _so_on_refresh(frm) {
    if (frm.doc.docstatus === 1) {
        // Submitted: show saved rows, or compute virtual if doc pre-dates the feature
        _dlits_submitted_display(frm);
    } else if (frm.is_new()) {
        // New doc: nothing saved yet, sync from items
        _so_schedule_sync(frm);
    } else {
        // Saved draft: Python validate already wrote correct rows; just render
        // DO NOT call _so_schedule_sync here — clear_table + add_child would dirty the form
        _dlits_render_summary(frm);
    }
}

function _so_schedule_sync(frm) {
    if (_so_margin_timer) clearTimeout(_so_margin_timer);
    _so_margin_timer = setTimeout(() => { _so_margin_timer = null; _dlits_sync_margin(frm); }, 600);
}

// ══ Shared implementation (identical in Quotation and SI files) ═══════════════

function _dlits_sync_margin(frm) {
    if (frm.doc.docstatus === 1) {
        _dlits_submitted_display(frm);
        return;
    }

    const items = (frm.doc.items || []).filter(r => r.item_code && flt(r.qty) > 0);
    if (!items.length) {
        frappe.model.clear_table(frm.doc, 'dlits_margin_table');
        frm.refresh_field('dlits_margin_table');
        _dlits_render_summary(frm);
        return;
    }

    const existing = {};
    (frm.doc.dlits_margin_table || []).forEach(row => {
        if (row.items_row_ref) existing[row.items_row_ref] = {
            cost: row.cost, discount_type: row.discount_type,
            discount: row.discount, is_non_stock: row.is_non_stock,
        };
    });

    const item_codes = [...new Set(items.map(r => r.item_code))];
    frappe.call({
        method: 'dlitscustom.override.margin_table_utils.get_item_costs',
        args:   { item_codes: JSON.stringify(item_codes) },
        callback(r) {
            const costs = (r && r.message) ? r.message : {};
            frappe.model.clear_table(frm.doc, 'dlits_margin_table');

            items.forEach(item => {
                const info = costs[item.item_code] || {};
                const prev = existing[item.name]   || {};
                const is_stock = !!info.is_stock_item;
                const rate = flt(item.rate), qty = flt(item.qty);

                let cost;
                if (is_stock)               cost = flt(info.cost);
                else if (prev.is_non_stock)  cost = flt(prev.cost);
                else                         cost = rate * 0.75;

                const discount_type = prev.discount_type || 'Percentage';
                const discount      = flt(prev.discount  || 0);
                const computed      = _dlits_compute_row(rate, qty, cost, discount_type, discount);

                const child = frappe.model.add_child(
                    frm.doc, 'Dlits Margin Table Item', 'dlits_margin_table'
                );
                child.item_code = item.item_code; child.item_name = item.item_name || '';
                child.qty = qty; child.rate = rate; child.cost = cost;
                child.discount_type = discount_type; child.discount = discount;
                child.is_non_stock = is_stock ? 0 : 1; child.items_row_ref = item.name;
                Object.assign(child, computed);
            });

            frm.refresh_field('dlits_margin_table');
            _dlits_render_summary(frm);
        },
    });
}

function _dlits_submitted_display(frm) {
    const saved_rows = frm.doc.dlits_margin_table || [];
    if (saved_rows.length > 0) {
        _dlits_render_summary(frm, saved_rows);
        return;
    }
    // Old submitted doc before the feature existed — compute virtual rows (no form dirty)
    const items = (frm.doc.items || []).filter(r => r.item_code && flt(r.qty) > 0);
    if (!items.length) { _dlits_render_summary(frm, []); return; }

    frappe.call({
        method: 'dlitscustom.override.margin_table_utils.get_item_costs',
        args:   { item_codes: JSON.stringify([...new Set(items.map(r => r.item_code))]) },
        callback(r) {
            const costs = (r && r.message) ? r.message : {};
            const virtual_rows = items.map(item => {
                const info = costs[item.item_code] || {};
                const rate = flt(item.rate), qty = flt(item.qty);
                const cost = info.is_stock_item ? flt(info.cost) : rate * 0.75;
                return _dlits_compute_row(rate, qty, cost, 'Percentage', 0);
            });
            _dlits_render_summary(frm, virtual_rows);
        },
    });
}

function _dlits_recalc_row(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    Object.assign(row, _dlits_compute_row(
        flt(row.rate), flt(row.qty), flt(row.cost),
        row.discount_type || 'Percentage', flt(row.discount || 0)
    ));
    frm.refresh_field('dlits_margin_table');
    _dlits_render_summary(frm);
}

function _dlits_compute_row(rate, qty, cost, discount_type, discount) {
    const amount        = rate * qty;
    const cost_amount   = cost * qty;
    const margin_amount = amount - cost_amount;
    const margin_pct    = amount ? (margin_amount / amount * 100) : 0;
    const net_rate = discount_type === 'Fixed Amount'
        ? Math.max(0, rate - discount)
        : Math.max(0, rate * (1 - discount / 100));
    const net_amount     = net_rate * qty;
    const net_margin     = net_amount - cost_amount;
    const net_margin_pct = net_amount ? (net_margin / net_amount * 100) : 0;
    return { amount, cost_amount, margin_amount, margin_pct,
             net_rate, net_amount, net_margin, net_margin_pct };
}

function _dlits_render_summary(frm, rows) {
    const fd = frm.fields_dict && frm.fields_dict.dlits_margin_summary;
    if (!fd || !fd.$wrapper) return;

    rows = rows || frm.doc.dlits_margin_table || [];

    let total_selling = 0, total_cost = 0, gross_margin = 0,
        net_amount_sum = 0, net_margin_sum = 0;

    rows.forEach(row => {
        total_selling  += flt(row.amount);
        total_cost     += flt(row.cost_amount);
        gross_margin   += flt(row.margin_amount);
        net_amount_sum += flt(row.net_amount);
        net_margin_sum += flt(row.net_margin);
    });

    const gross_pct = total_selling  ? (gross_margin  / total_selling  * 100) : 0;
    const net_pct   = net_amount_sum ? (net_margin_sum / net_amount_sum * 100) : 0;

    let add_disc = 0;
    const raw_disc = flt(frm.doc.discount_amount || 0);
    if (raw_disc > 0) {
        if ((frm.doc.apply_discount_on || 'Grand Total') === 'Grand Total') {
            const gt_before = flt(frm.doc.grand_total || 0) + raw_disc;
            add_disc = gt_before
                ? raw_disc * flt(frm.doc.net_total || total_selling) / gt_before
                : raw_disc;
        } else {
            add_disc = raw_disc;
        }
    }

    const final_margin = net_margin_sum - add_disc;
    const final_base   = net_amount_sum - add_disc;
    const final_pct    = final_base > 0 ? (final_margin / final_base * 100) : 0;

    const cur = frm.doc.currency || 'SAR';
    function fmt(n) {
        return cur + ' ' + n.toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2});
    }
    function clr(n)   { return n >= 0 ? '#2e7d32' : '#c62828'; }
    function badge(n)  { return '<span style="font-size:11px;margin-left:4px;color:' + clr(n) + '">(' + n.toFixed(1) + '%)</span>'; }

    function card(label, val_html, highlight) {
        const b = highlight
            ? 'background:var(--primary-light,#e8eaf6);border:2px solid var(--primary-color,#2e3092)'
            : 'background:var(--card-bg,#f8f9fa);border:1px solid var(--border-color,#e0e0e0)';
        return '<div style="flex:1;min-width:150px;' + b + ';border-radius:6px;padding:9px 13px">'
            + '<div style="font-size:11px;color:var(--text-muted,#888);margin-bottom:2px">' + label + '</div>'
            + '<div style="font-size:14px;font-weight:600">' + val_html + '</div></div>';
    }

    const cards = [
        card('Total Selling', '<span>' + fmt(total_selling) + '</span>'),
        card('Total Cost',    '<span>' + fmt(total_cost)    + '</span>'),
        card('Gross Margin',
            '<span style="color:' + clr(gross_margin) + '">' + fmt(gross_margin) + '</span>' + badge(gross_pct)
        ),
        card('Net Margin (row disc.)',
            '<span style="color:' + clr(net_margin_sum) + '">' + fmt(net_margin_sum) + '</span>' + badge(net_pct)
        ),
    ];

    if (add_disc > 0) {
        const disc_label = 'Doc Discount <span style="font-size:10px">('
            + (frm.doc.apply_discount_on || 'Grand Total') + ')</span>';
        cards.push(
            '<div style="flex:1;min-width:150px;background:var(--card-bg,#f8f9fa);'
            + 'border:1px dashed #e53935;border-radius:6px;padding:9px 13px">'
            + '<div style="font-size:11px;color:var(--text-muted,#888);margin-bottom:2px">' + disc_label + '</div>'
            + '<div style="font-size:14px;font-weight:600;color:#e53935">&minus; ' + fmt(add_disc) + '</div></div>'
        );
        cards.push(card('Final Net Margin',
            '<span style="color:' + clr(final_margin) + '">' + fmt(final_margin) + '</span>' + badge(final_pct),
            true
        ));
    }

    fd.$wrapper.html(
        '<div style="display:flex;gap:7px;flex-wrap:wrap;padding:5px 0 2px">'
        + cards.join('') + '</div>'
    );
}
