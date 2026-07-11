import frappe


DSTR_PRINT_HTML = """
{%- macro fdate(d) -%}{{ frappe.format_date(d, 'dd MMM yyyy') }}{%- endmacro -%}

{%- set sc = {
  "Draft":"#6c757d","Pending Approval":"#fd7e14","Approved":"#28a745",
  "Rejected":"#dc3545","Delivered":"#0d6efd","Received":"#6f42c1",
  "Completed":"#198754","Cancelled":"#dc3545"
} -%}
{%- set approver_name = frappe.db.get_value("User", doc.approved_by, "full_name") if doc.approved_by else "" -%}

<head>
<meta charset="UTF-8">
<style>
@font-face {
  font-family: 'SaudiRiyal';
  src: url('data:font/woff2;base64,d09GMgABAAAAAAL4AA0AAAAAB2wAAAKjAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP0ZGVE0cGh4GYACCXhEICoF0gWELDgABNgIkAxgEIAWFLAdFG2MGERWc38h+HsbOiCl5Nj4EoyffxZWpjtZ+BF92z3+fmb37AEYAEQpfYOViJMdCIf77T6c+i+iBZC3snGA/Y17uMju8JhWrQXNFJX7imvqJDVSNb/JEuTVtFik0jQYf7nxgVRqlRRvCwHxgtGHbiDKyXm5kcj0JAV/fYRx8883du/cO1ERjJCFUhAIJOZ+Jiyqkm9JbuABGxy96RzWunahr4gjxk/zm/z8jMrIgwNxWIL+4pQALZIGWCkNQXVVJEtr+5P9/B9WfM/9/26QiC9UBhEyURAYiIQEAggL6bIj/qwNKUBMVTMZSQAEIhJByzjX6B5i6PW68s6nVt9zTIubF2Tkxn+vyva92qJ6Aht50ej5YWv3AI03gxTfcECdPRsR8qwHg/kOuvd8pdRxu0tF8YfUPPZa/1bUPOiZjzNwnPmkXLZY0eOTxrGLnO8aYn3rs/6uPg9aW/dOls7qP7zNUgY1zvvr1jsMBAkGLB+a9tLzOkF+r1ii88r2Q389QVQLhZeYU5yZqnV8OZQGIuUBCcc6rAqVREkgAAKjvcwHobIEAoYZbBUiqeFGArIbPBCjU8I8AFTWirQClGjFGgGpqxzYBqmsez3BmUVTDPKjE0NhHTGp7UMwa+4EF+gcqWFQFS7SLWE3LmPH46vrEUXy1ZTFYXMxKo0cEZoYrkESCJLTuLo7plXKF0eDE0gxMsw/pohQe+spvWjU9CTbjBSUJJZqT5IrRsE7T9wCzkUmipLorvREOs1dOSaneyzdxYJZUbsKRHrS1tb6t9Wn1PKnesFgSGJPGAMlvcFMzjmj+8vrgLHYD40jCiMmlhJUlI9/NRN6YnZh0IpdlNFCN18gTmV0sfxxxCCDxbymJJEWWoyjX83dbmMpeURqGkVVWoWEAAA==') format('woff2');
  font-weight: normal; font-style: normal;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body {
  font-family: 'SaudiRiyal', 'Noto Sans', Arial, 'Liberation Sans', sans-serif;
  font-size: 10.5pt; color: #2c3e50; background: #fff;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.print-format { margin-top: 1mm !important; margin-left: 2mm !important; margin-right: 2mm !important; padding: 0 !important; }
body { margin: 0 !important; padding: 0 !important; }
thead { display: table-header-group; }
.lbl { font-size: 7pt; text-transform: uppercase; letter-spacing: 0.8px; color: #90a4ae; }
.badge {
  display: inline-block; padding: 2px 9px; border-radius: 20px;
  font-size: 6.5pt; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin-top: 2px;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
.sec-title {
  font-size: 7pt; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1.5px; color: #5a4fcf;
  padding-bottom: 3px; border-bottom: 1.5px solid #667eea; margin-bottom: 5px;
}
table.inv-tbl { width: 100%; border-collapse: collapse; font-size: 10pt; margin-bottom: 5px; table-layout: fixed; }
table.inv-tbl thead { display: table-header-group; }
table.inv-tbl thead th {
  background: linear-gradient(135deg, #e8ecfd 0%, #edddf7 100%);
  color: #3d2fa0; padding: 5px; font-size: 8pt; font-weight: 600;
  text-transform: uppercase; text-align: left; letter-spacing: 0.2px;
  border-bottom: 1px solid rgba(102,126,234,0.25);
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
table.inv-tbl thead th.c { text-align: center; }
table.inv-tbl tbody tr { border-bottom: 1px solid #e8e4f5; page-break-inside: avoid; }
table.inv-tbl tbody tr:nth-child(even) { background: #fafaff; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
table.inv-tbl tbody td { padding: 4px 5px; vertical-align: top; word-wrap: break-word; overflow-wrap: break-word; }
table.inv-tbl tbody td.c { text-align: center; }
.item-desc { font-size: 9pt; color: #607d8b; margin-top: 2px; line-height: 1.45; }
.item-desc p { margin: 0 0 2px 0; }
.info-box { border: 1px solid #e4e0f5; }
.info-box-hd { background: #f0eeff; color: #5a4fcf; padding: 3px 10px; font-size: 7pt; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid #ddd8f8; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.info-box-bd { padding: 7px 10px; }
.info-row { display: flex; margin-bottom: 3px; font-size: 9pt; }
.info-lbl { color: #90a4ae; width: 110px; flex-shrink: 0; font-size: 7.5pt; padding-top: 1px; }
.info-val { font-weight: 600; color: #2c3e50; }
.note-wrap { border: 1px solid #e4e0f5; margin-bottom: 5px; }
.note-hd { background: #f0eeff; color: #5a4fcf; padding: 3px 10px; font-size: 7pt; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; border-bottom: 1px solid #ddd8f8; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.note-bd { padding: 6px 10px; font-size: 9.5pt; color: #546e7a; }
@media print {
  * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .footer-bar { display: none; }
}
@page {
  @bottom-center {
    content: "DLITS (Alejtihadat Trading Est.)  \\2022  Ph: 920009447  \\2022  dlits-sa.com  \\2022  info@dlits-sa.com  |  Stock Transfer Document  |  Page " counter(page) " / " counter(pages);
    font-size: 5pt; color: #90a4ae; font-family: Arial, sans-serif;
    border-top: 1px solid #e4e0f5; padding-top: 3px; text-align: center; white-space: nowrap;
  }
}
</style>
</head>

<body>

<!-- ═══ HEADER ══════════════════════════════════════════════════════ -->
<div id="header-html" class="hidden-pdf">
  <table style="width:100%;border-collapse:collapse;">
    <tr>
      <td style="width:12%;vertical-align:middle;padding:0 6px 0 0;">
        <img src="/files/Dlits300Logo.jpg" alt="DLITS" style="width:68px;height:auto;max-width:100%;">
      </td>
      <td style="width:51%;vertical-align:top;padding:0 6px;">
        <div style="font-size:11pt;font-weight:700;color:#1b078d;line-height:1.1;">DLITS (Alejtihadat Trading Est.)</div>
        <div style="font-size:9pt;color:#607d8b;line-height:1.5;margin-top:2px;">مؤسسة الاجتهادات التجارية</div>
        <div style="font-size:6.5pt;color:#607d8b;line-height:1.5;margin-top:2px;">
          Khalid Ibn Al Waleed Str.(6904), Ash Sharafiyah Dist. JED KSA<br>
          P.O 23216 &bull; C.R 4030136701 &bull; Ph: 920009447 &bull; info@dlits-sa.com
        </div>
      </td>
      <td style="width:37%;vertical-align:top;text-align:right;padding:0 0 0 6px;">
        <div style="font-size:8pt;font-weight:700;color:#667eea;line-height:1.2;">
          {% if doc.request_type == "Return" %}Stock Return Request / طلب إرجاع مخزون{% else %}Stock Transfer Request / طلب نقل مخزون{% endif %}
        </div>
        <div style="font-size:11pt;font-weight:700;color:#2c3e50;margin-top:1px;letter-spacing:0.3px;">{{ doc.name }}</div>
        <div style="font-size:7pt;color:#607d8b;margin-top:1px;">{{ fdate(doc.request_date) }}</div>
        <span class="badge" style="background:{{ sc.get(doc.status,'#6c757d') }};color:#fff;">{{ doc.status }}</span>
      </td>
    </tr>
  </table>
</div>

<div style="border-top:1px solid rgba(102,126,234,0.35);margin-bottom:6px;"></div>

{% if doc.request_type == "Return" %}
<div style="background:#FFF3E0;border:1px solid #FFB74D;padding:4px 10px;margin-bottom:6px;font-size:8.5pt;font-weight:700;color:#E65100;border-radius:2px;-webkit-print-color-adjust:exact;print-color-adjust:exact;">
  &#9651; RETURN REQUEST — Items are being returned to warehouse / طلب إرجاع أصناف إلى المستودع
</div>
{% endif %}

<!-- ═══ INFO SECTION ════════════════════════════════════════════════ -->
<table style="width:100%;border-collapse:collapse;margin-bottom:6px;">
  <tr>
    <td style="width:49%;vertical-align:top;padding-right:5px;">
      <div class="info-box">
        <div class="info-box-hd">Requester &nbsp;|&nbsp; الطالب</div>
        <div class="info-box-bd">
          <div class="info-row"><span class="info-lbl">Name / الاسم</span><span class="info-val">{{ doc.receiver_name or doc.requested_by }}</span></div>
          <div class="info-row"><span class="info-lbl">Request Date</span><span class="info-val">{{ fdate(doc.request_date) }}</span></div>
          <div class="info-row"><span class="info-lbl">Deliver To</span><span class="info-val">{{ doc.deliver_to_warehouse or "—" }}</span></div>
          {% if doc.reference_type and doc.reference_name %}
          <div class="info-row"><span class="info-lbl">{{ doc.reference_type }}</span><span class="info-val">{{ doc.reference_name }}</span></div>
          {% endif %}
          {% if doc.request_notes %}
          <div style="margin-top:5px;font-size:8.5pt;color:#546e7a;font-style:italic;border-top:1px solid #f0eeff;padding-top:4px;">{{ doc.request_notes }}</div>
          {% endif %}
        </div>
      </div>
    </td>
    <td style="width:2%;"></td>
    <td style="width:49%;vertical-align:top;">
      <div class="info-box">
        <div class="info-box-hd">Approval &amp; Dispatch &nbsp;|&nbsp; الموافقة والإرسال</div>
        <div class="info-box-bd">
          <div class="info-row"><span class="info-lbl">Approved By</span><span class="info-val">{{ approver_name or doc.approved_by or "—" }}</span></div>
          <div class="info-row"><span class="info-lbl">Approval Date</span><span class="info-val">{{ fdate(doc.approval_date) if doc.approval_date else "—" }}</span></div>
          <div class="info-row"><span class="info-lbl">Dispatch From</span><span class="info-val">{{ doc.dispatch_warehouse or "—" }}</span></div>
          {% if doc.dispatch_users %}
          <div class="info-row"><span class="info-lbl">Dispatch Users</span><span class="info-val">{{ doc.dispatch_users | map(attribute='full_name') | select | join(', ') or doc.dispatch_users | map(attribute='user') | join(', ') }}</span></div>
          {% endif %}
          {% if doc.cost_center %}
          <div class="info-row"><span class="info-lbl">Cost Center</span><span class="info-val">{{ doc.cost_center }}</span></div>
          {% endif %}
          {% if doc.delivery_date %}
          <div class="info-row"><span class="info-lbl">Delivered On</span><span class="info-val">{{ fdate(doc.delivery_date) }}</span></div>
          {% endif %}
          {% if doc.received_date %}
          <div class="info-row"><span class="info-lbl">Received On</span><span class="info-val">{{ fdate(doc.received_date) }}</span></div>
          {% endif %}
        </div>
      </div>
    </td>
  </tr>
</table>

<hr style="border:none;border-top:1px solid #e4e0f5;margin-bottom:5px;">

<!-- ═══ ITEMS TABLE ══════════════════════════════════════════════════ -->
<div class="sec-title">Items &amp; Quantities &nbsp;|&nbsp; الأصناف والكميات</div>

<table class="inv-tbl">
  <colgroup>
    <col style="width:26px">
    <col>
    <col style="width:44px">
    <col style="width:50px">
  </colgroup>
  <thead>
    <tr>
      <th>#</th>
      <th>Item &nbsp;<span style="font-weight:400;opacity:.9;font-size:6.5pt;">الصنف</span></th>
      <th class="c">Qty<br><span style="font-weight:400;opacity:.9;font-size:6.5pt;">الكمية</span></th>
      <th class="c">UOM<br><span style="font-weight:400;opacity:.9;font-size:6.5pt;">الوحدة</span></th>
    </tr>
  </thead>
  <tbody>
    {% for item in doc.items %}
    {%- set item_doc = frappe.get_doc("Item", item.item_code) -%}
    <tr>
      <td style="color:#90a4ae;font-size:9pt;padding-top:5px;">{{ loop.index }}</td>
      <td>
        <div style="overflow:hidden;">
          {%- if item_doc.image -%}
          <div style="float:left;width:42px;height:42px;overflow:hidden;border-radius:3px;border:1px solid #e4e0f5;margin-right:6px;margin-bottom:2px;-webkit-print-color-adjust:exact;print-color-adjust:exact;">
            <img src="{{ item_doc.image }}" style="width:42px !important;height:42px !important;max-width:none !important;object-fit:cover;display:block;">
          </div>
          {%- endif -%}
          <div style="font-size:10pt;font-weight:700;color:#2c3e50;line-height:1.3;">
            {%- if item_doc.brand -%}<span style="color:#607d8b;font-weight:500;">{{ item_doc.brand }}</span> &bull; {%- endif -%}{{ item.item_code }}
          </div>
          {%- if item.item_name and item.item_name != item.item_code -%}
          <div class="item-desc">{{ item.item_name }}</div>
          {%- endif -%}
          {%- if item_doc.description -%}
          <div class="item-desc">{{ item_doc.description | striptags }}</div>
          {%- endif -%}
          {%- if item.remarks -%}
          <div class="item-desc" style="font-style:italic;color:#90a4ae;">{{ item.remarks | striptags }}</div>
          {%- endif -%}
        </div>
      </td>
      <td class="c" style="font-size:10pt;font-weight:600;">{{ "%.0f" | format(item.qty) if item.qty == item.qty|int else "%.2f" | format(item.qty) }}</td>
      <td class="c" style="font-size:8.5pt;color:#546e7a;">{{ item.uom or "" }}</td>
    </tr>
    {% endfor %}
  </tbody>
</table>

<div style="font-size:8pt;color:#90a4ae;text-align:right;margin-bottom:4px;padding-right:2px;">
  Total Items / إجمالي الأصناف: <strong style="color:#546e7a;">{{ doc.items | length }}</strong>
</div>

<hr style="border:none;border-top:1px solid #e4e0f5;margin-bottom:5px;">

{% if doc.approval_notes or doc.delivery_notes %}
<div style="margin-bottom:8px;">
  {% if doc.approval_notes %}
  <div class="note-wrap">
    <div class="note-hd">Approval Notes &nbsp;|&nbsp; ملاحظات الموافقة</div>
    <div class="note-bd">{{ doc.approval_notes }}</div>
  </div>
  {% endif %}
  {% if doc.delivery_notes %}
  <div class="note-wrap">
    <div class="note-hd">Delivery Notes &nbsp;|&nbsp; ملاحظات التسليم</div>
    <div class="note-bd">{{ doc.delivery_notes }}</div>
  </div>
  {% endif %}
</div>
{% endif %}

<!-- ═══ SIGNATURES ═══════════════════════════════════════════════════ -->
<table style="width:100%;border-collapse:collapse;margin-top:8px;font-size:8.5pt;color:#607d8b;page-break-inside:avoid;">
  <tr>
    <td style="width:32%;text-align:center;border:1px solid #e4e0f5;padding:28px 10px 6px;">
      Requested By &nbsp;|&nbsp; الطالب<br>
      <span style="font-size:8pt;color:#90a4ae;">{{ doc.receiver_name or doc.requested_by }}</span>
    </td>
    <td style="width:2%;"></td>
    <td style="width:32%;text-align:center;border:1px solid #e4e0f5;padding:28px 10px 6px;">
      Approved &amp; Dispatched By &nbsp;|&nbsp; المعتمد<br>
      <span style="font-size:8pt;color:#90a4ae;">{{ approver_name or doc.approved_by or "" }}</span>
    </td>
    <td style="width:2%;"></td>
    <td style="width:32%;text-align:center;border:1px solid #e4e0f5;padding:28px 10px 6px;">
      Received By &nbsp;|&nbsp; المستلم<br>
      <span style="font-size:8pt;color:#90a4ae;">{{ doc.receiver_name or doc.requested_by }}</span>
    </td>
  </tr>
</table>

<!-- ═══ SCREEN FOOTER (hidden in PDF) ══════════════════════════════ -->
<div class="footer-bar" style="border-top:1px solid #e4e0f5;padding-top:4px;text-align:center;font-size:6.5pt;color:#90a4ae;margin-top:8px;">
  DLITS (Alejtihadat Trading Est.) &bull; Ph: 920009447 &bull; dlits-sa.com &bull; info@dlits-sa.com
</div>

</body>
"""


def create_dlits_workflow():
	"""Create (or update) the Dlits Stock Transfer workflow."""
	wf_name = "Dlits Stock Transfer"
	doc_type = "Dlits Stock Transfer Request"

	states = [
		{"state": "Draft",            "doc_status": "0", "allow_edit": "All",                         "avoid_status_override": 1, "is_optional_state": 0},
		{"state": "Pending Approval", "doc_status": "0", "allow_edit": "Shb Stock Transfer Approver",  "avoid_status_override": 0, "is_optional_state": 0},
		{"state": "Approved",         "doc_status": "0", "allow_edit": "All",                         "avoid_status_override": 0, "is_optional_state": 0},
		{"state": "Rejected",         "doc_status": "0", "allow_edit": "All",                         "avoid_status_override": 0, "is_optional_state": 1},
		{"state": "Delivered",        "doc_status": "0", "allow_edit": "All",                         "avoid_status_override": 0, "is_optional_state": 0},
		{"state": "Received",         "doc_status": "0", "allow_edit": "Shb Stock Transfer Approver",  "avoid_status_override": 0, "is_optional_state": 0},
		{"state": "Completed",        "doc_status": "1", "allow_edit": "Shb Stock Transfer Approver",  "avoid_status_override": 0, "is_optional_state": 0},
		{"state": "Cancelled",        "doc_status": "2", "allow_edit": "Shb Stock Transfer Approver",  "avoid_status_override": 0, "is_optional_state": 0},
	]

	transitions = [
		{"state": "Draft",            "action": "Request Approval", "next_state": "Pending Approval", "allowed": "All",                          "allow_self_approval": 1, "condition": ""},
		{"state": "Pending Approval", "action": "Approve",          "next_state": "Approved",         "allowed": "Shb Stock Transfer Approver",  "allow_self_approval": 1, "condition": ""},
		{"state": "Pending Approval", "action": "Reject",           "next_state": "Rejected",         "allowed": "Shb Stock Transfer Approver",  "allow_self_approval": 1, "condition": ""},
		{"state": "Rejected",         "action": "Revise",           "next_state": "Draft",            "allowed": "All",                          "allow_self_approval": 1, "condition": ""},
		{"state": "Approved",         "action": "Mark Delivered",   "next_state": "Delivered",        "allowed": "All",                          "allow_self_approval": 1, "condition": "frappe.session.user in [d.user for d in doc.dispatch_users] or frappe.db.get_value('Has Role', {'parent': frappe.session.user, 'role': 'Shb Stock Transfer Approver'})"},
		{"state": "Delivered",        "action": "Confirm Receipt",  "next_state": "Received",         "allowed": "All",                          "allow_self_approval": 1, "condition": "frappe.session.user == doc.requested_by or frappe.db.get_value('Has Role', {'parent': frappe.session.user, 'role': 'Shb Stock Transfer Approver'})"},
		{"state": "Received",         "action": "Complete",         "next_state": "Completed",        "allowed": "Shb Stock Transfer Approver",  "allow_self_approval": 1, "condition": ""},
		{"state": "Completed",        "action": "Cancel",           "next_state": "Cancelled",        "allowed": "Shb Stock Transfer Approver",  "allow_self_approval": 1, "condition": ""},
	]

	if frappe.db.exists("Workflow", wf_name):
		wf = frappe.get_doc("Workflow", wf_name)
		wf.states = []
		wf.transitions = []
	else:
		wf = frappe.new_doc("Workflow")
		wf.workflow_name = wf_name
		wf.document_type = doc_type
		wf.workflow_state_field = "status"
		wf.override_status = 1
		wf.send_email_alert = 0
		wf.is_active = 1

	for s in states:
		wf.append("states", s)
	for t in transitions:
		wf.append("transitions", t)

	# ignore_links: states are child rows not yet in DB when transitions are validated
	wf.flags.ignore_links = True
	if wf.is_new():
		wf.insert(ignore_permissions=True)
		print(f"Created workflow: {wf_name}")
	else:
		wf.save(ignore_permissions=True)
		print(f"Updated workflow: {wf_name}")

	frappe.db.commit()



def fix_report_modules():
	"""Fix reports whose module was set to the wrong app (e.g. Stock instead of dlitscustom)."""
	reports = frappe.db.get_all(
		"Report",
		filters={"name": ["like", "Dlits%"], "module": ["!=", "dlitscustom"]},
		fields=["name", "module"],
	)
	for r in reports:
		frappe.db.set_value("Report", r.name, "module", "dlitscustom")
		print(f"Fixed {r.name}: {r.module} → dlitscustom")
	frappe.db.commit()
	print("Done.")


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
			"margin_top": 5,
			"margin_bottom": 10,
			"margin_left": 5,
			"margin_right": 5,
		}).insert(ignore_permissions=True)
		print(f"Created print format: {pf_name}")

	frappe.db.commit()


def update_dlits_workspace():
	"""Add Stock Transfer Management section to the DLITS Custom workspace."""
	import json

	ws = frappe.get_doc("Workspace", "DLITS Custom")

	# ── Content (visual layout) ────────────────────────────────────────────────
	content = json.loads(ws.content or "[]")

	existing_ids = {item.get("id") for item in content}
	if "header_st" not in existing_ids:
		st_content = [
			{
				"id": "header_st",
				"type": "header",
				"data": {"text": '<span class="h4"><b>Stock Transfer Management</b></span>', "col": 12},
			},
			{"id": "shortcut_st1", "type": "shortcut", "data": {"shortcut_name": "Stock Transfer Requests", "col": 3}},
		]
		content = st_content + content
		content.append({"id": "card_st", "type": "card", "data": {"card_name": "Stock Transfer Management", "col": 4}})
		ws.content = json.dumps(content)

	# ── Links (sidebar card content) ──────────────────────────────────────────
	existing_labels = {lnk.label for lnk in ws.links}
	if "Stock Transfer Management" not in existing_labels:
		for link in [
			{
				"hidden": 0, "is_query_report": 0,
				"label": "Stock Transfer Management",
				"link_count": 1, "link_type": "DocType",
				"onboard": 1, "type": "Card Break",
			},
			{
				"hidden": 0, "is_query_report": 0,
				"label": "Dlits Stock Transfer Request",
				"link_to": "Dlits Stock Transfer Request",
				"link_count": 0, "link_type": "DocType",
				"onboard": 1, "type": "Link",
			},
		]:
			ws.append("links", link)

	# ── Shortcuts (top quick-access tiles) ────────────────────────────────────
	existing_sc = {sc.label for sc in ws.shortcuts}
	if "Stock Transfer Requests" not in existing_sc:
		ws.append("shortcuts", {
			"color": "#2e3092", "doc_view": "List",
			"label": "Stock Transfer Requests",
			"link_to": "Dlits Stock Transfer Request",
			"type": "DocType",
		})

	# ── Roles (who sees the workspace) ────────────────────────────────────────
	existing_roles = {r.role for r in ws.roles}
	for role in ["Shb Basic User", "Stock User", "Stock Manager"]:
		if role not in existing_roles:
			ws.append("roles", {"role": role})

	ws.save(ignore_permissions=True)
	frappe.db.commit()
	print("Workspace updated: Stock Transfer Management section added.")


def zatca_check_credentials():
	"""Check ZATCA Business Settings credentials and certificate state."""
	rows = frappe.get_all(
		"ZATCA Business Settings",
		fields=["name", "company", "fatoora_server", "status",
		        "enable_zatca_integration", "type_of_business_transactions",
		        "security_token", "secret",
		        "production_security_token", "production_secret",
		        "compliance_request_id", "production_request_id"],
		limit=5,
	)
	print("=== ZATCA Business Settings ===")
	for r in rows:
		print(f"  company:                  {r.company}")
		print(f"  fatoora_server:           {r.fatoora_server}")
		print(f"  status:                   {r.status}")
		print(f"  enable_zatca_integration: {r.enable_zatca_integration}")
		print(f"  type_of_biz_transactions: {r.type_of_business_transactions}")
		print(f"  compliance_request_id:    {r.compliance_request_id}")
		print(f"  production_request_id:    {r.production_request_id}")
		print(f"  has compliance token:     {bool(r.security_token)}")
		print(f"  has compliance secret:    {bool(r.secret)}")
		print(f"  has PRODUCTION token:     {bool(r.production_security_token)}")
		print(f"  has PRODUCTION secret:    {bool(r.production_secret)}")
		print()

	# Check ksa_compliance zatca_api.py to understand how it builds auth
	print("=== ZATCA Integration Log — last 5 (any status) ===")
	logs = frappe.get_all(
		"ZATCA Integration Log",
		fields=["name", "status", "zatca_http_status_code", "invoice_additional_fields_reference", "creation"],
		order_by="creation desc",
		limit=8,
	)
	for lg in logs:
		print(f"  {lg.creation}  HTTP {lg.zatca_http_status_code}  {lg.status}  → {lg.invoice_additional_fields_reference}")


def old_zatca_check_credentials():
	"""Check ZATCA Business Settings credentials and certificate expiry."""
	# Check Phase 2 settings
	try:
		settings = frappe.get_all(
			"ZATCA Phase 2 Business Settings",
			fields=["name", "company", "environment", "certificate_validity_date",
			        "api_url", "otp", "signed_certificate_csid",
			        "private_key", "secret"],
			limit=5,
		)
		print("=== ZATCA Phase 2 Business Settings ===")
		for s in settings:
			print(f"  company: {s.company}")
			print(f"  environment: {s.get('environment', '?')}")
			print(f"  api_url: {s.get('api_url', '?')}")
			print(f"  certificate_validity_date: {s.get('certificate_validity_date', 'NOT SET')}")
			has_cert   = bool(s.get("signed_certificate_csid") or s.get("secret"))
			has_key    = bool(s.get("private_key"))
			print(f"  has CSID/secret: {has_cert}")
			print(f"  has private key: {has_key}")
			print()
	except Exception as e:
		print(f"Error reading Phase 2 settings: {e}")

	# Also check raw ZATCA message for more detail
	print("=== Raw zatca_message from DB ===")
	rows = frappe.db.sql("""
		SELECT invoice_additional_fields_reference, zatca_http_status_code,
		       zatca_message, zatca_status
		FROM `tabZATCA Integration Log`
		WHERE invoice_additional_fields_reference IN (
			'IN2607J1S006373-AdditionalFields-8733',
			'IN2607J1S006372-AdditionalFields-8731'
		)
		ORDER BY creation DESC LIMIT 4
	""", as_dict=True)
	for r in rows:
		print(f"  {r.invoice_additional_fields_reference}")
		print(f"    HTTP {r.zatca_http_status_code} | zatca_status: {r.zatca_status}")
		print(f"    message: {r.zatca_message}")


def zatca_rejection_details2():
	"""Fetch ZATCA rejection reasons from ZATCA Integration Log."""
	names = [
		"IN2607J1S006373-AdditionalFields-8733",
		"RT-IN2607J2S001180-AdditionalFields-8732",
		"IN2607J1S006372-AdditionalFields-8731",
		"RT-IN2607J1S002010-AdditionalFields-8730",
	]
	for n in names:
		print("=" * 70)
		print("DOC:", n)
		logs = frappe.get_all(
			"ZATCA Integration Log",
			filters={"invoice_additional_fields_reference": n},
			fields=["name", "status", "zatca_status", "zatca_http_status_code", "zatca_message"],
			order_by="creation desc",
			limit=3,
		)
		if not logs:
			print("  No ZATCA Integration Log found.")
		for lg in logs:
			print(f"  HTTP: {lg.zatca_http_status_code}  status: {lg.status}  zatca_status: {lg.zatca_status}")
			print(f"  MESSAGE: {str(lg.zatca_message or '')[:2000]}")


def zatca_rejection_details():
	"""Fetch ZATCA API rejection reason from comments + log on the 4 rejected docs."""
	names = [
		"IN2607J1S006373-AdditionalFields-8733",
		"RT-IN2607J2S001180-AdditionalFields-8732",
		"IN2607J1S006372-AdditionalFields-8731",
		"RT-IN2607J1S002010-AdditionalFields-8730",
	]
	for n in names:
		print("=" * 70)
		print("DOC:", n)
		# comments
		comments = frappe.get_all(
			"Comment",
			filters={"reference_doctype": "Sales Invoice Additional Fields", "reference_name": n},
			fields=["comment_type", "content", "creation"],
			order_by="creation desc",
			limit=5,
		)
		for c in comments:
			print(f"  [{c.comment_type}] {c.content[:1500]}")
		if not comments:
			print("  (no comments)")
		# Also check if there is a ZATCA log / integration details child
		try:
			logs = frappe.get_all(
				"ZATCA Integration Details",
				filters={"sales_invoice_additional_fields": n},
				fields=["name", "result_message", "rejection_reason", "response"],
				order_by="creation desc", limit=3,
			)
			for lg in logs:
				print(f"  LOG: {lg}")
		except Exception:
			pass


def check_zatca_rejections():
	"""Print details of the latest ZATCA-rejected Sales Invoice Additional Fields docs."""
	rows = frappe.get_all(
		"Sales Invoice Additional Fields",
		filters={"integration_status": "Rejected", "is_latest": 1},
		fields=["name", "sales_invoice", "invoice_doctype", "invoice_type_code",
		        "invoice_type_transaction", "integration_status",
		        "validation_messages", "validation_errors", "modified"],
		order_by="modified desc",
		limit=10,
	)
	for r in rows:
		print("=" * 60)
		for k, v in r.items():
			if v:
				print(f"  {k}: {str(v)[:500]}")
		# Also check Comments for ZATCA response details
		comments = frappe.db.sql("""
			SELECT content FROM `tabComment`
			WHERE reference_doctype='Sales Invoice Additional Fields'
			  AND reference_name=%s
			ORDER BY creation DESC LIMIT 5
		""", r.name, as_dict=True)
		for c in comments:
			print(f"  COMMENT: {str(c.content)[:800]}")


def check_margin_links():
	"""Debug: list all DocType Link rows involving Dlits Margin Table Item."""
	rows = frappe.db.sql(
		"SELECT name, parent, link_doctype, link_fieldname, is_child_table, "
		"table_fieldname, parent_doctype, custom "
		"FROM `tabDocType Link` "
		"WHERE link_doctype LIKE '%Margin%' OR parent_doctype LIKE '%Margin%' "
		"   OR (parent='Item' AND link_doctype LIKE '%Dlits%') "
		"ORDER BY parent, link_doctype",
		as_dict=True,
	)
	for r in rows:
		print(dict(r))
	print(f"Total: {len(rows)}")


def fix_margin_connections():
	"""
	Remove auto-created DocType Link rows for Dlits Margin Table Item on
	Sales Order, Sales Invoice, and Quotation.  These rows cause Item connections
	to filter through the margin child table instead of the standard items table,
	showing only 1 result instead of all.
	"""
	# Frappe auto-creates a DocType Link whenever a child table has a Link field.
	# Our margin table (Dlits Margin Table Item) has item_code → Item, so Frappe
	# created links: SO/SI/Quotation → Item through the margin table.
	# These OVERRIDE the standard SO Item / SI Item links in the Connections tab.
	deleted = frappe.db.sql(
		"DELETE FROM `tabDocType Link` "
		"WHERE link_doctype = 'Dlits Margin Table Item' "
		"   AND link_fieldname = 'item_code'",
	)
	frappe.db.commit()
	frappe.clear_cache()
	print(f"Deleted DocType Link rows for Dlits Margin Table Item.item_code → Item.")


def rebuild_dlits_workspace():
	"""
	Completely rebuild the DLITS Custom workspace from scratch.
	Organized into 6 sections: Stock Transfer, Commission, Sales, Financial Reports,
	Customer Followup, Pricing — with shortcut tiles at the top and cards below.
	Safe to re-run: deletes the old workspace doc and recreates it.
	"""
	import json

	# ── Content (visual layout) ────────────────────────────────────────────────
	content = [
		# ── Stock Transfer ──────────────────────────────────────────────────
		{"id": "h_st",   "type": "header",   "data": {"text": '<span class="h4"><b>Stock Transfer Management</b></span>', "col": 12}},
		{"id": "sc_st1", "type": "shortcut", "data": {"shortcut_name": "Stock Transfer Requests", "col": 3}},
		{"id": "sc_st2", "type": "shortcut", "data": {"shortcut_name": "Stock Balance",           "col": 3}},
		# ── Commission ──────────────────────────────────────────────────────
		{"id": "h_cm",   "type": "header",   "data": {"text": '<span class="h4"><b>Commission Management</b></span>', "col": 12}},
		{"id": "sc_cm1", "type": "shortcut", "data": {"shortcut_name": "Sales Partners",       "col": 3}},
		{"id": "sc_cm2", "type": "shortcut", "data": {"shortcut_name": "Commission Mgmt",      "col": 3}},
		{"id": "sc_cm3", "type": "shortcut", "data": {"shortcut_name": "Commission Payments",  "col": 3}},
		{"id": "sc_cm4", "type": "shortcut", "data": {"shortcut_name": "Commission Report",    "col": 3}},
		# ── Sales Transactions ───────────────────────────────────────────────
		{"id": "h_sl",   "type": "header",   "data": {"text": '<span class="h4"><b>Sales Transactions</b></span>', "col": 12}},
		{"id": "sc_si",  "type": "shortcut", "data": {"shortcut_name": "Sales Invoice",     "col": 3}},
		{"id": "sc_so",  "type": "shortcut", "data": {"shortcut_name": "Sales Order",       "col": 3}},
		{"id": "sc_qt",  "type": "shortcut", "data": {"shortcut_name": "Quotation",         "col": 3}},
		{"id": "sc_cf",  "type": "shortcut", "data": {"shortcut_name": "Customer Followup", "col": 3}},
		# ── Financial Reports ────────────────────────────────────────────────
		{"id": "h_fr",   "type": "header",   "data": {"text": '<span class="h4"><b>Financial Reports</b></span>', "col": 12}},
		{"id": "sc_tx",  "type": "shortcut", "data": {"shortcut_name": "Tax Report",      "col": 3}},
		{"id": "sc_sa",  "type": "shortcut", "data": {"shortcut_name": "Sales Analytics", "col": 3}},
		{"id": "sc_ar",  "type": "shortcut", "data": {"shortcut_name": "AR Report",       "col": 3}},
		{"id": "sc_ars", "type": "shortcut", "data": {"shortcut_name": "AR Summary",      "col": 3}},
		# ── All Modules (cards) ──────────────────────────────────────────────
		{"id": "h_all",  "type": "header",   "data": {"text": '<span class="h4"><b>All Modules</b></span>', "col": 12}},
		{"id": "cd_st",  "type": "card",     "data": {"card_name": "Stock Transfer Management", "col": 4}},
		{"id": "cd_cm",  "type": "card",     "data": {"card_name": "Commission Management",     "col": 4}},
		{"id": "cd_sl",  "type": "card",     "data": {"card_name": "Sales Transactions",        "col": 4}},
		{"id": "cd_pm",  "type": "card",     "data": {"card_name": "Pricing Management",        "col": 4}},
		{"id": "cd_cf",  "type": "card",     "data": {"card_name": "Customer Followup",         "col": 4}},
		{"id": "cd_fr",  "type": "card",     "data": {"card_name": "Financial Reports",         "col": 4}},
	]

	# ── Shortcuts (colored tiles) ──────────────────────────────────────────────
	shortcuts = [
		# Stock Transfer
		{"label": "Stock Transfer Requests", "link_to": "Dlits Stock Transfer Request", "type": "DocType", "color": "#2e3092", "doc_view": "List"},
		{"label": "Stock Balance",           "link_to": "Dlits Stock Balance",          "type": "Report",  "color": "#fd7e14", "doc_view": ""},
		# Commission
		{"label": "Sales Partners",       "link_to": "Dlits Sales Partner",        "type": "DocType", "color": "#8e44ad", "doc_view": "List"},
		{"label": "Commission Mgmt",      "link_to": "Dlits Commission Management", "type": "DocType", "color": "#6f42c1", "doc_view": "List"},
		{"label": "Commission Payments",  "link_to": "Dlits Commission Payment",   "type": "DocType", "color": "#9b59b6", "doc_view": "List"},
		{"label": "Commission Report",    "link_to": "Dlits Commission Report",    "type": "Report",  "color": "#7952b3", "doc_view": ""},
		# Sales Transactions
		{"label": "Sales Invoice",     "link_to": "Sales Invoice",          "type": "DocType", "color": "#e74c3c", "doc_view": "List"},
		{"label": "Sales Order",       "link_to": "Sales Order",            "type": "DocType", "color": "#27ae60", "doc_view": "List"},
		{"label": "Quotation",         "link_to": "Quotation",              "type": "DocType", "color": "#fd7e14", "doc_view": "List"},
		{"label": "Customer Followup", "link_to": "Dlits Customer Followup","type": "DocType", "color": "#17a2b8", "doc_view": "List"},
		# Financial Reports
		{"label": "Tax Report",      "link_to": "DLITS Tax Report",                  "type": "Report", "color": "#6f42c1", "doc_view": ""},
		{"label": "Sales Analytics", "link_to": "DLITS Sales Analytics",             "type": "Report", "color": "#e83e8c", "doc_view": ""},
		{"label": "AR Report",       "link_to": "DLITS Accounts Receivable",         "type": "Report", "color": "#2e7d32", "doc_view": ""},
		{"label": "AR Summary",      "link_to": "DLITS Accounts Receivable Summary", "type": "Report", "color": "#1565c0", "doc_view": ""},
	]

	# ── Links (card content) ───────────────────────────────────────────────────
	links = [
		# Stock Transfer Management card
		{"type": "Card Break", "label": "Stock Transfer Management", "link_count": 2, "link_type": "DocType", "onboard": 1, "hidden": 0, "is_query_report": 0},
		{"type": "Link", "label": "Dlits Stock Transfer Request", "link_to": "Dlits Stock Transfer Request", "link_type": "DocType", "is_query_report": 0, "onboard": 1,  "hidden": 0},
		{"type": "Link", "label": "Stock Balance",                "link_to": "Dlits Stock Balance",          "link_type": "Report",  "is_query_report": 1, "onboard": 0,  "hidden": 0},
		# Commission Management card
		{"type": "Card Break", "label": "Commission Management", "link_count": 4, "link_type": "DocType", "onboard": 1, "hidden": 0, "is_query_report": 0},
		{"type": "Link", "label": "Dlits Sales Partner",         "link_to": "Dlits Sales Partner",         "link_type": "DocType", "is_query_report": 0, "onboard": 1, "hidden": 0},
		{"type": "Link", "label": "Dlits Commission Management", "link_to": "Dlits Commission Management",  "link_type": "DocType", "is_query_report": 0, "onboard": 1, "hidden": 0},
		{"type": "Link", "label": "Dlits Commission Payment",    "link_to": "Dlits Commission Payment",    "link_type": "DocType", "is_query_report": 0, "onboard": 0, "hidden": 0},
		{"type": "Link", "label": "Commission Report",           "link_to": "Dlits Commission Report",     "link_type": "Report",  "is_query_report": 1, "onboard": 0, "hidden": 0},
		# Sales Transactions card
		{"type": "Card Break", "label": "Sales Transactions", "link_count": 4, "link_type": "DocType", "onboard": 0, "hidden": 0, "is_query_report": 0},
		{"type": "Link", "label": "Sales Order",   "link_to": "Sales Order",   "link_type": "DocType", "is_query_report": 0, "onboard": 0, "hidden": 0},
		{"type": "Link", "label": "Sales Invoice", "link_to": "Sales Invoice", "link_type": "DocType", "is_query_report": 0, "onboard": 0, "hidden": 0},
		{"type": "Link", "label": "Quotation",     "link_to": "Quotation",     "link_type": "DocType", "is_query_report": 0, "onboard": 0, "hidden": 0},
		{"type": "Link", "label": "Customer",      "link_to": "Customer",      "link_type": "DocType", "is_query_report": 0, "onboard": 0, "hidden": 0},
		# Pricing Management card
		{"type": "Card Break", "label": "Pricing Management", "link_count": 2, "link_type": "DocType", "onboard": 0, "hidden": 0, "is_query_report": 0},
		{"type": "Link", "label": "Pricing Rule Dlits", "link_to": "Pricing Rule Dlits", "link_type": "DocType", "is_query_report": 0, "onboard": 0, "hidden": 0},
		{"type": "Link", "label": "Item Price",         "link_to": "Item Price",         "link_type": "DocType", "is_query_report": 0, "onboard": 0, "hidden": 0},
		# Customer Followup card
		{"type": "Card Break", "label": "Customer Followup", "link_count": 3, "link_type": "DocType", "onboard": 0, "hidden": 0, "is_query_report": 0},
		{"type": "Link", "label": "Dlits Customer Followup",           "link_to": "Dlits Customer Followup",                    "link_type": "DocType", "is_query_report": 0, "onboard": 0, "hidden": 0},
		{"type": "Link", "label": "Customer Followup Report",          "link_to": "Dlits Customer Followup",                    "link_type": "Report",  "is_query_report": 1, "onboard": 0, "hidden": 0},
		{"type": "Link", "label": "Customer Acquisition and Loyalty",  "link_to": "Dlits Customer Acquisition and Loyalty",     "link_type": "Report",  "is_query_report": 1, "onboard": 0, "hidden": 0},
		# Financial Reports card
		{"type": "Card Break", "label": "Financial Reports", "link_count": 4, "link_type": "Report", "onboard": 0, "hidden": 0, "is_query_report": 0},
		{"type": "Link", "label": "Tax Report",        "link_to": "DLITS Tax Report",                  "link_type": "Report", "is_query_report": 1, "onboard": 0, "hidden": 0},
		{"type": "Link", "label": "Sales Analytics",   "link_to": "DLITS Sales Analytics",             "link_type": "Report", "is_query_report": 1, "onboard": 0, "hidden": 0},
		{"type": "Link", "label": "Accounts Receivable","link_to": "DLITS Accounts Receivable",        "link_type": "Report", "is_query_report": 1, "onboard": 0, "hidden": 0},
		{"type": "Link", "label": "AR Summary",        "link_to": "DLITS Accounts Receivable Summary", "link_type": "Report", "is_query_report": 1, "onboard": 0, "hidden": 0},
	]

	roles = [
		"System Manager", "Accounts Manager", "Accounts User",
		"Sales Manager",  "Purchase Manager",
		"Shb Basic User", "Stock User", "Stock Manager",
		"Shb Stock Transfer Approver", "Shb Commission Approver",
	]

	# ── Write to DB ────────────────────────────────────────────────────────────
	if frappe.db.exists("Workspace", "DLITS Custom"):
		ws = frappe.get_doc("Workspace", "DLITS Custom")
		ws.links    = []
		ws.shortcuts = []
		ws.roles    = []
	else:
		ws = frappe.new_doc("Workspace")
		ws.name  = "DLITS Custom"
		ws.label = "DLITS Custom"
		ws.title = "DLITS Custom"

	ws.module         = "dlitscustom"
	ws.icon           = "layers"
	ws.indicator_color = "blue"
	ws.is_hidden      = 0
	ws.public         = 1
	ws.sequence_id    = 1.0
	ws.parent_page    = ""
	ws.content        = json.dumps(content)

	for sc in shortcuts:
		ws.append("shortcuts", sc)
	for lnk in links:
		ws.append("links", lnk)
	for role in roles:
		ws.append("roles", {"role": role})

	ws.save(ignore_permissions=True)
	frappe.db.commit()
	print("DLITS Custom workspace rebuilt with all modules.")
