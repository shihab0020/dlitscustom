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
