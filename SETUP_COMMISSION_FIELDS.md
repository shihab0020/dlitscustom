# Setup Commission Fields

## Step 1: Create Custom Fields

Run this in your ERPNext console:

```bash
bench --site your-site-name console
```

Then execute:

```python
# Create commission custom fields
from dlitscustom.fixtures.custom_fields import create_commission_custom_fields
create_commission_custom_fields()

# Commit to database
import frappe
frappe.db.commit()

print("Commission fields created successfully!")
```

## Step 2: Verify Fields Created

After running the above, you should see these new fields in:

### Sales Invoice:
- **DLITS Commission** section (collapsible)
- DLITS Sales Partner (Link field)
- Commission Type (Select - read only)
- Commission Rate (Float - read only)
- Commission Amount (Currency - read only)
- Commission Paid Amount (Currency - editable after submit)
- Outstanding Commission (Currency - read only)

### Sales Order:
- **DLITS Commission** section (collapsible)
- DLITS Sales Partner (Link field)
- Commission Type (Select - read only)
- Commission Rate (Float - read only)
- Commission Amount (Currency - read only)

## Step 3: Test the Setup

1. **Create a DLITS Sales Partner:**
   - Go to DLITS Custom workspace
   - Click "DLITS Sales Partner"
   - Create a new partner with commission settings

2. **Test in Sales Invoice:**
   - Create a new Sales Invoice
   - You should see the "DLITS Commission" section
   - Select a DLITS Sales Partner
   - Commission should auto-calculate

3. **Test Commission Payment Tracking:**
   - Submit the Sales Invoice
   - Use "Update Commission Paid" button to track payments
   - Commission outstanding should update automatically

## Alternative: Run Installation Script

If the above doesn't work, you can run the full installation:

```bash
bench --site your-site-name console
```

```python
from dlitscustom.install import after_install
after_install()
```

This will create all custom fields, workspace, and setup everything.

## Troubleshooting

If you get "Unknown column" errors:
1. Make sure custom fields are created first
2. Clear cache: `bench --site your-site-name clear-cache`
3. Restart: `bench restart`
4. Reload the forms in browser

The commission system uses our **custom DLITS Sales Partner** DocType, not ERPNext's built-in Sales Partner. This gives us full control over commission management.