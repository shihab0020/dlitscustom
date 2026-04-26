import frappe


DSTR_PRINT_HTML = """
<style>
.dstr{font-family:Arial,sans-serif;font-size:12px;color:#333;max-width:820px;margin:0 auto}
.dstr-hd{display:flex;justify-content:space-between;align-items:flex-start;padding-bottom:14px;border-bottom:3px solid #2e3092;margin-bottom:16px}
.dstr-co{font-size:20px;font-weight:700;color:#2e3092}
.dstr-co-sub{font-size:10px;color:#888;margin-top:3px}
.dstr-doc-no{font-size:14px;font-weight:700}
.dstr-doc-title{font-size:16px;font-weight:700;margin-bottom:4px}
.dstr-badge{display:inline-block;padding:3px 11px;border-radius:10px;color:#fff;font-size:11px;font-weight:700}
.dstr-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px}
.dstr-box{border:1px solid #dee2e6;border-radius:4px;padding:10px 12px}
.dstr-box-hd{font-size:10px;text-transform:uppercase;color:#888;font-weight:700;border-bottom:1px solid #eee;padding-bottom:5px;margin-bottom:8px}
.dstr-r{display:flex;margin-bottom:3px;font-size:11px}
.dstr-l{color:#888;width:128px;flex-shrink:0}
.dstr-v{font-weight:600}
.dstr-tbl{width:100%;border-collapse:collapse;font-size:11px;margin-bottom:14px}
.dstr-tbl th{background:#2e3092;color:#fff;padding:7px 8px;text-align:left}
.dstr-tbl th.r,.dstr-tbl td.r{text-align:right}
.dstr-tbl td{padding:6px 8px;border-bottom:1px solid #eee}
.dstr-tbl tr:nth-child(even) td{background:#f9f9f9}
.dstr-note{border:1px solid #dee2e6;border-radius:3px;padding:8px 10px;margin-bottom:8px;background:#fafafa;font-size:11px}
.dstr-note-hd{font-weight:700;color:#555;font-size:10px;text-transform:uppercase;margin-bottom:4px}
.dstr-sigs{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;margin-top:32px}
.dstr-sig{border-top:1px solid #333;padding-top:6px;text-align:center;font-size:11px}
.dstr-sig-name{color:#888;margin-top:2px;font-size:10px}
.return-banner{background:#fff3cd;border:1px solid #ffc107;padding:6px 12px;margin-bottom:12px;font-size:11px;color:#856404;border-radius:3px;font-weight:600}
</style>

{% set sc = {
  "Draft":"#6c757d","Pending Approval":"#fd7e14","Approved":"#28a745",
  "Rejected":"#dc3545","Delivered":"#0d6efd","Received":"#6f42c1",
  "Completed":"#198754","Cancelled":"#dc3545"
} %}

<div class="dstr">

  <div class="dstr-hd">
    <div>
      <div class="dstr-co">{{ doc.company }}</div>
      <div class="dstr-co-sub">Stock Transfer Management</div>
    </div>
    <div style="text-align:right">
      <div class="dstr-doc-title">
        {% if doc.request_type == "Return" %}Stock Return Request{% else %}Stock Transfer Request{% endif %}
      </div>
      <div class="dstr-doc-no">{{ doc.name }}</div>
      <div style="font-size:11px;color:#888;margin:2px 0">{{ frappe.format(doc.request_date, "Date") }}</div>
      <span class="dstr-badge" style="background:{{ sc.get(doc.status,'#6c757d') }}">{{ doc.status }}</span>
    </div>
  </div>

  {% if doc.request_type == "Return" %}
  <div class="return-banner">&#9651; RETURN REQUEST — Items are being returned from site to warehouse</div>
  {% endif %}

  <div class="dstr-grid">

    <div class="dstr-box">
      <div class="dstr-box-hd">Requester / Technician</div>
      <div class="dstr-r"><span class="dstr-l">Name</span><span class="dstr-v">{{ doc.technician_name or doc.requested_by }}</span></div>
      <div class="dstr-r"><span class="dstr-l">Request Date</span><span class="dstr-v">{{ frappe.format(doc.request_date, "Date") }}</span></div>
      <div class="dstr-r"><span class="dstr-l">Deliver To</span><span class="dstr-v">{{ doc.destination_warehouse or "—" }}</span></div>
      {% if doc.reference_type and doc.reference_name %}
      <div class="dstr-r"><span class="dstr-l">{{ doc.reference_type }}</span><span class="dstr-v">{{ doc.reference_name }}</span></div>
      {% endif %}
      {% if doc.technician_notes %}
      <div style="margin-top:6px;font-size:10px;color:#555;font-style:italic">{{ doc.technician_notes }}</div>
      {% endif %}
    </div>

    <div class="dstr-box">
      <div class="dstr-box-hd">Approval &amp; Dispatch</div>
      <div class="dstr-r"><span class="dstr-l">Supervisor</span><span class="dstr-v">{{ doc.assigned_supervisor or "—" }}</span></div>
      <div class="dstr-r"><span class="dstr-l">Dispatch From</span><span class="dstr-v">{{ doc.source_warehouse or "—" }}</span></div>
      <div class="dstr-r"><span class="dstr-l">Showroom User</span><span class="dstr-v">{{ doc.assigned_showroom_user or "—" }}</span></div>
      {% if doc.approval_date %}
      <div class="dstr-r"><span class="dstr-l">Approved On</span><span class="dstr-v">{{ frappe.format(doc.approval_date, "Date") }}</span></div>
      {% endif %}
      {% if doc.delivery_date %}
      <div class="dstr-r"><span class="dstr-l">Delivered On</span><span class="dstr-v">{{ frappe.format(doc.delivery_date, "Date") }}</span></div>
      {% endif %}
      {% if doc.received_date %}
      <div class="dstr-r"><span class="dstr-l">Received On</span><span class="dstr-v">{{ frappe.format(doc.received_date, "Date") }}</span></div>
      {% endif %}
      {% if doc.stock_entry %}
      <div class="dstr-r"><span class="dstr-l">Stock Entry</span><span class="dstr-v">{{ doc.stock_entry }}</span></div>
      {% endif %}
    </div>

  </div>

  <table class="dstr-tbl">
    <thead>
      <tr>
        <th style="width:4%">#</th>
        <th style="width:16%">Item Code</th>
        <th style="width:28%">Item Name</th>
        <th class="r" style="width:9%">Req. Qty</th>
        <th style="width:7%">UOM</th>
        <th class="r" style="width:9%">Delivered</th>
        <th class="r" style="width:9%">Received</th>
        <th style="width:18%">Remarks</th>
      </tr>
    </thead>
    <tbody>
      {% for item in doc.items %}
      <tr>
        <td>{{ loop.index }}</td>
        <td>{{ item.item_code }}</td>
        <td>{{ item.item_name }}</td>
        <td class="r">{{ item.qty }}</td>
        <td>{{ item.uom or "" }}</td>
        <td class="r">{{ item.delivered_qty if item.delivered_qty else "—" }}</td>
        <td class="r">{{ item.received_qty if item.received_qty else "—" }}</td>
        <td style="font-size:10px;color:#777">{{ item.remarks or "" }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  {% if doc.supervisor_notes or doc.showroom_notes %}
  <div style="margin-bottom:14px">
    {% if doc.supervisor_notes %}
    <div class="dstr-note"><div class="dstr-note-hd">Supervisor Notes</div>{{ doc.supervisor_notes }}</div>
    {% endif %}
    {% if doc.showroom_notes %}
    <div class="dstr-note"><div class="dstr-note-hd">Delivery Notes</div>{{ doc.showroom_notes }}</div>
    {% endif %}
  </div>
  {% endif %}

  <div class="dstr-sigs">
    <div class="dstr-sig">
      <div>Requested By</div>
      <div class="dstr-sig-name">{{ doc.technician_name or doc.requested_by }}</div>
    </div>
    <div class="dstr-sig">
      <div>Approved &amp; Dispatched By</div>
      <div class="dstr-sig-name">{{ doc.assigned_supervisor or "" }}</div>
    </div>
    <div class="dstr-sig">
      <div>Received By</div>
      <div class="dstr-sig-name">{{ doc.technician_name or doc.requested_by }}</div>
    </div>
  </div>

</div>
"""


def create_dlits_print_formats():
	"""Run once to create the Dlits Stock Transfer print format in the database."""
	pf_name = "Dlits Stock Transfer Print"

	if frappe.db.exists("Print Format", pf_name):
		doc = frappe.get_doc("Print Format", pf_name)
		doc.html = DSTR_PRINT_HTML
		doc.save(ignore_permissions=True)
		print(f"Updated print format: {pf_name}")
	else:
		frappe.get_doc({
			"doctype": "Print Format",
			"name": pf_name,
			"doc_type": "Dlits Stock Transfer Request",
			"print_format_type": "Jinja",
			"html": DSTR_PRINT_HTML,
			"standard": "Yes",
			"module": "Dlitscustom",
			"margin_top": 15,
			"margin_bottom": 15,
			"margin_left": 15,
			"margin_right": 15,
		}).insert(ignore_permissions=True)
		print(f"Created print format: {pf_name}")

	frappe.db.commit()


def update_dlits_workspace():
	"""Add Stock Transfer Management section to the DLITS Custom workspace."""
	import json

	ws = frappe.get_doc("Workspace", "DLITS Custom")

	# ── Content (visual layout) ────────────────────────────────────────────────
	content = json.loads(ws.content or "[]")

	# Only add if not already present
	existing_ids = {item.get("id") for item in content}
	if "header_st" not in existing_ids:
		st_content = [
			{
				"id": "header_st",
				"type": "header",
				"data": {"text": '<span class="h4"><b>Stock Transfer Management</b></span>', "col": 12},
			},
			{"id": "shortcut_st1", "type": "shortcut", "data": {"shortcut_name": "Stock Transfer Requests", "col": 3}},
			{"id": "shortcut_st2", "type": "shortcut", "data": {"shortcut_name": "Warehouse User Assignment", "col": 3}},
		]
		# Insert at top so it's the first section
		content = st_content + content
		# Add the card entry into the cards row (append to existing card row)
		content.append({"id": "card_st", "type": "card", "data": {"card_name": "Stock Transfer Management", "col": 4}})
		ws.content = json.dumps(content)

	# ── Links (sidebar card content) ──────────────────────────────────────────
	existing_labels = {lnk.label for lnk in ws.links}
	if "Stock Transfer Management" not in existing_labels:
		for link in [
			{
				"hidden": 0, "is_query_report": 0,
				"label": "Stock Transfer Management",
				"link_count": 2, "link_type": "DocType",
				"onboard": 1, "type": "Card Break",
			},
			{
				"hidden": 0, "is_query_report": 0,
				"label": "Dlits Stock Transfer Request",
				"link_to": "Dlits Stock Transfer Request",
				"link_count": 0, "link_type": "DocType",
				"onboard": 1, "type": "Link",
			},
			{
				"hidden": 0, "is_query_report": 0,
				"label": "Dlits Warehouse User Assignment",
				"link_to": "Dlits Warehouse User Assignment",
				"link_count": 0, "link_type": "DocType",
				"onboard": 0, "type": "Link",
			},
		]:
			ws.append("links", link)

	# ── Shortcuts (top quick-access tiles) ────────────────────────────────────
	existing_sc = {sc.label for sc in ws.shortcuts}
	for sc in [
		{
			"color": "#2e3092", "doc_view": "List",
			"label": "Stock Transfer Requests",
			"link_to": "Dlits Stock Transfer Request",
			"type": "DocType",
		},
		{
			"color": "#17a2b8", "doc_view": "List",
			"label": "Warehouse User Assignment",
			"link_to": "Dlits Warehouse User Assignment",
			"type": "DocType",
		},
	]:
		if sc["label"] not in existing_sc:
			ws.append("shortcuts", sc)

	# ── Roles (who sees the workspace) ────────────────────────────────────────
	existing_roles = {r.role for r in ws.roles}
	for role in ["Shb Basic User", "Stock User", "Stock Manager"]:
		if role not in existing_roles:
			ws.append("roles", {"role": role})

	ws.save(ignore_permissions=True)
	frappe.db.commit()
	print("Workspace updated: Stock Transfer Management section added.")
