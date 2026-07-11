import frappe
from dlitscustom.override.margin_table_utils import get_item_costs
import json


def migrate_item_ref():
    """One-time migration: copy item_code → item_ref for rows saved before the field rename."""
    frappe.db.sql("""
        UPDATE `tabDlits Margin Table Item`
        SET item_ref = item_code
        WHERE (item_ref IS NULL OR item_ref = '')
          AND item_code IS NOT NULL
          AND item_code != ''
    """)
    frappe.db.commit()
    count = frappe.db.sql("SELECT COUNT(*) FROM `tabDlits Margin Table Item` WHERE item_ref IS NOT NULL AND item_ref != %s", ('',))[0][0]
    null_count = frappe.db.sql("SELECT COUNT(*) FROM `tabDlits Margin Table Item` WHERE (item_ref IS NULL OR item_ref = %s)", ('',))[0][0]
    print(f"Migration done. With item_ref: {count}, Missing item_ref: {null_count}")


def sync_margin_table(doc, method=None):
    """
    Server-side margin table sync. Runs on validate for Quotation, Sales Order, Sales Invoice.
    Mirrors the JS sync logic so margin data is always correct in the DB regardless of JS state.
    Non-stock item costs edited by the user are preserved from existing rows.
    """
    if not hasattr(doc, "dlits_margin_table"):
        return

    items = [r for r in (doc.items or []) if r.item_code and (r.qty or 0) > 0]

    if not items:
        doc.set("dlits_margin_table", [])
        return

    # Preserve user-edited cost / discount for non-stock items
    existing = {}
    for row in doc.dlits_margin_table or []:
        if row.get("items_row_ref"):
            existing[row.items_row_ref] = {
                "cost":          row.cost,
                "discount_type": row.discount_type,
                "discount":      row.discount,
                "is_non_stock":  row.is_non_stock,
            }

    item_codes = list({r.item_code for r in items})
    costs = get_item_costs(json.dumps(item_codes))

    doc.set("dlits_margin_table", [])

    for item in items:
        info = costs.get(item.item_code, {})
        prev = existing.get(item.name, {})

        is_stock   = bool(info.get("is_stock_item"))
        rate       = float(item.rate or 0)
        qty        = float(item.qty  or 0)

        if is_stock:
            # max(last_purchase_rate, custom_rfq_price) — already resolved in get_item_costs
            cost = float(info.get("cost", 0))
        elif prev.get("is_non_stock"):
            cost = float(prev.get("cost") or 0)
        else:
            cost = rate * 0.75

        discount_type = prev.get("discount_type") or "Percentage"
        discount      = float(prev.get("discount") or 0)

        amount        = rate * qty
        cost_amount   = cost * qty
        margin_amount = amount - cost_amount
        margin_pct    = (margin_amount / amount * 100) if amount else 0

        net_rate = max(0, rate - discount) if discount_type == "Fixed Amount" \
                   else max(0, rate * (1 - discount / 100))

        net_amount     = net_rate * qty
        net_margin     = net_amount - cost_amount
        net_margin_pct = (net_margin / net_amount * 100) if net_amount else 0

        doc.append("dlits_margin_table", {
            "item_ref":      item.item_code,
            "item_name":     item.item_name or "",
            "qty":           qty,
            "rate":          rate,
            "cost":          cost,
            "discount_type": discount_type,
            "discount":      discount,
            "is_non_stock":  0 if is_stock else 1,
            "items_row_ref": item.name,
            "amount":        amount,
            "cost_amount":   cost_amount,
            "margin_amount": margin_amount,
            "margin_pct":    margin_pct,
            "net_rate":      net_rate,
            "net_amount":    net_amount,
            "net_margin":    net_margin,
            "net_margin_pct": net_margin_pct,
        })
