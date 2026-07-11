// ── Dlits Margin — Quotation ──────────────────────────────────────────────────
// Python validate hook (margin_sync.py) is authoritative — populates dlits_margin_table on save.
// JS is display-only: renders summary from saved rows; recalcs locally on discount edits.
// Submitted docs with no saved rows (pre-feature) get a virtual display via frappe.call.

frappe.ui.form.on('Quotation', {
    setup(frm) {
        // ERPNext's setup (fires before ours) calls set_indicator_formatter("item_code").
        // That scans all child tables and may land on Dlits Margin Table Item.item_code
        // (type=Data, options=null) → slug(null) crash during grid render.
        // Delete the formatter right here — before any grid render ever happens.
        const _df = frappe.meta.get_docfield('Dlits Margin Table Item', 'item_code');
        if (_df) delete _df.formatter;
    },
    refresh(frm)                        { _dlits_render_summary(frm); },
    discount_amount(frm)                { _dlits_render_summary(frm); },
    additional_discount_percentage(frm) { _dlits_render_summary(frm); },
    apply_discount_on(frm)              { _dlits_render_summary(frm); },
});

frappe.ui.form.on('Dlits Margin Table Item', {
    cost(frm, cdt, cdn)         { if (frm.doctype === 'Quotation') _dlits_recalc_row(frm, cdt, cdn); },
    discount_type(frm, cdt, cdn){ if (frm.doctype === 'Quotation') _dlits_recalc_row(frm, cdt, cdn); },
    discount(frm, cdt, cdn)     { if (frm.doctype === 'Quotation') _dlits_recalc_row(frm, cdt, cdn); },
});

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

function _dlits_virtual_display(frm) {
    // Submitted doc saved before margin feature was activated — compute display-only virtual rows.
    const items = (frm.doc.items || []).filter(r => r.item_code && flt(r.qty) > 0);
    if (!items.length) return;
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

function _dlits_render_summary(frm, rows) {
    const fd = frm.fields_dict && frm.fields_dict.dlits_margin_summary;
    if (!fd || !fd.$wrapper) return;

    rows = rows || frm.doc.dlits_margin_table || [];

    if (!rows.length) {
        if (frm.is_new()) {
            fd.$wrapper.html('<div style="color:var(--text-muted,#888);font-size:12px;padding:4px 0">Save the document to see margin analysis.</div>');
        } else if (frm.doc.docstatus === 1) {
            _dlits_virtual_display(frm);
        } else {
            fd.$wrapper.html('');
        }
        return;
    }

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
    function clr(n)  { return n >= 0 ? '#2e7d32' : '#c62828'; }
    function badge(n){ return '<span style="font-size:11px;margin-left:4px;color:' + clr(n) + '">(' + n.toFixed(1) + '%)</span>'; }

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
