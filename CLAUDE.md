# CLAUDE.md — dlitscustom Project Context

## Overview
Custom Frappe/ERPNext app for **DLITS** (Saudi Arabia company).  
App name: `dlitscustom` | Publisher: shihab | Email: shihab@dlits-sa.com  
App color: `#2e3092` (dark blue)

## Dev Environment
- Bench path: `/home/dlits/frappe-bench`
- Active site: `dlits2025` (previous dev site: `dlitsdev1`)
- Git branch: `develop` → merges to `main`
- Git user: shihab0020

### Common bench commands
```bash
# Run a function
bench --site dlits2025 execute dlitscustom.print_setup.create_dlits_workflow

# Build/migrate
bench --site dlits2025 migrate
bench build --app dlitscustom

# Start bench
bench start

# Push to remote
git push -u origin develop
```

### Performance tuning (already applied)
- Gunicorn workers: `-w 4` (was 9), in `/home/dlits/frappe-bench/config/supervisor.conf`
- MariaDB `innodb_buffer_pool_size` tuned in `/etc/mysql/mariadb.conf.d/50-server.cnf`
- Redis on port `11000`

---

## Custom Doctypes

### Dlits Stock Transfer Request
**File:** `dlitscustom/dlitscustom/doctype/dlits_stock_transfer_request/dlits_stock_transfer_request.py`  
Manages stock movement requests from technicians/site staff to warehouse managers.

**Workflow states:** Draft → Pending Approval → Approved → Delivered → Received → Completed  
**Workflow name:** `Dlits Stock Transfer`  
**Approver role:** `Shb Stock Transfer Approver`

Key fields: `request_type` (Transfer/Return), `dispatch_warehouse`, `deliver_to_warehouse`,  
`dispatch_users` (child table), `items` (child table: `Dlits Stock Transfer Item`),  
`approved_by`, `approval_date`, `delivery_date`, `received_date`, `stock_entry`

On submit → creates a **Stock Entry** (Material Transfer)  
Print format: `Dlits Stock Transfer Print` (defined in `print_setup.py`)

Child doctypes:
- `dlits_stock_transfer_item` — items with qty, delivered_qty, received_qty
- `dlits_stock_transfer_dispatch_user` — assigned dispatch users

Whitelist functions:
- `make_stock_transfer_from_so(source_name)` — create from Sales Order
- `make_stock_transfer_from_project(project)` — create from Project
- `get_items_from_sales_order(sales_order)`

### Dlits Customer Followup
**File:** `dlitscustom/dlitscustom/doctype/dlits_customer_followup/dlits_customer_followup.py`

Tracks customer debt collection follow-ups. On update, syncs status/date/aging back to:
- `Customer` master: `custom_last_followup_status`, `custom_last_followup_date`, `custom_followup_aging`
- Outstanding `Sales Invoice` records: `custom_last_followup_status`, `custom_last_followup_date`, `custom_followup_aging_days`

Child doctypes:
- `dlits_followup_update` — interaction log rows (outcome, update_date)
- `dlits_followup_linked_document` — linked invoices/orders (balance_amount)
- `dlits_followup_participant` — participants in followup

### Commission Module
- `dlits_commission_management` — commission configuration
- `dlits_commission_invoice` — commission invoice
- `dlits_commission_payment` — commission payment

### Sales Partner Module
- `dlits_sales_partner` — sales partner master
- `dlits_sales_partner_member` — member child table

### Pricing Rule Doctypes (custom breakdowns)
- `pricing_rule_dlits`, `pricing_rule_brand_dlits`, `pricing_rule_customer_dlits`
- `pricing_rule_customer_group_dlits`, `pricing_rule_item_code_dlits`, `pricing_rule_item_group_dlits`

---

## JS Customizations (hooks.py)
Injected into standard ERPNext doctypes:

| Doctype | JS Files |
|---------|----------|
| Sales Order | `sales_order_pricing_rule_dlits.js`, `sales_order_dlits_stock_transfer.js` |
| Sales Invoice | `sales_invoice_pricing_rule_dlits.js`, `sales_invoice_dlits_commission.js`, `sales_invoice_dlits_followup.js` |
| Project | `project_dlits_stock_transfer.js` |
| Payment Entry | `payment_entry_dlits.js` |
| Journal Entry | `journal_entry_dlits.js` |
| Customer | `customer.js` |
| Quotation | `quotation.js` |
| Dlits Sales Partner | `dlits_sales_partner.js` |

List JS: `Dlits Stock Transfer Request`, `Customer`, `Sales Invoice`

---

## Key Utility Files
- `dlitscustom/print_setup.py` — print formats, workflow creation, workspace setup
- `dlitscustom/shbnote.txt` — developer notes and commands reference

## Workspace
- Workspace name: `DLITS Custom`
- Roles: `Shb Basic User`, `Stock User`, `Stock Manager`
- `update_dlits_workspace()` in `print_setup.py` manages workspace content
