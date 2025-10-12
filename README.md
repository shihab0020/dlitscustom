# DLITS Custom App

A comprehensive ERPNext custom app for advanced pricing rules and sales partner commission management.

## Features

### 🏷️ Advanced Pricing Rules (Pricing Rule Dlits)
- **4 Base Price Types**: Price List Rate, Valuation Rate, Selling Rate, Item Rate
- **Flexible Discount Options**: Percentage and amount-based discounts
- **Smart Validation**: Automatic validation based on price type selection
- **Item Rate Support**: Direct item rate pricing without discount calculations
- **Production-Ready Logging**: Clean console logging for pricing rule applications

### 🤝 Sales Partner Management
- **Automatic Supplier Linking**: Auto-create suppliers for sales partners
- **Commission Tracking**: Built-in commission management
- **Custom Fields**: Enhanced sales partner profiles with supplier integration

### 📊 Comprehensive Reporting
- **Pricing Rules Analysis**: Interactive report with filtering and export capabilities
- **DLITS Sales Partner Commission Report**: Detailed commission tracking and payment management

### 🏢 Integrated Workspace
- **DLITS Custom Workspace**: Centralized access to all features
- **Quick Shortcuts**: Easy navigation to key functions
- **User-Friendly Interface**: Organized layout for efficient workflow

## Installation

### Prerequisites
- ERPNext v13+ or v14+
- Frappe Framework
- Administrator access to ERPNext site

### Quick Installation

1. **Navigate to your Frappe bench directory:**
   ```bash
   cd /path/to/your/frappe-bench
   ```

2. **Get the app:**
   ```bash
   bench get-app https://github.com/your-repo/dlitscustom
   ```

3. **Install on your site:**
   ```bash
   bench --site your-site-name install-app dlitscustom
   ```

4. **Restart and migrate:**
   ```bash
   bench restart
   bench --site your-site-name migrate
   ```

### Manual Installation

If you have the app files locally:

1. **Copy app to apps directory:**
   ```bash
   cp -r dlitscustom /path/to/frappe-bench/apps/
   ```

2. **Install the app:**
   ```bash
   cd /path/to/frappe-bench
   bench --site your-site-name install-app dlitscustom
   ```

3. **Complete setup:**
   ```bash
   bench restart
   bench --site your-site-name migrate
   ```

## Post-Installation Setup

### 1. Verify Installation
After installation, check that the following components are available:

- **Workspace**: Navigate to "DLITS Custom" workspace
- **DocType**: Access "Pricing Rule Dlits" from the workspace
- **Reports**: Check "Pricing Rules Analysis" and "DLITS Sales Partner Commission Report"
- **Custom Fields**: Verify Sales Partner has "Supplier" and "Auto Create Supplier" fields

### 2. Initial Configuration

#### Sales Partner Setup
1. Go to **Sales Partner** list
2. Create or edit existing sales partners
3. Enable "Auto Create Supplier" for automatic supplier creation
4. Link existing suppliers if needed

#### Pricing Rules Setup
1. Navigate to **Pricing Rule Dlits** from the workspace
2. Create your first pricing rule:
   - Select appropriate **Base Price Type**
   - Configure **Apply On** (Item Code, Item Group, Brand)
   - Set **Discount Percentage** or **Discount Amount**
   - For **Item Rate** type, no discount configuration needed

### 3. Testing the Setup

#### Test Pricing Rules
1. Create a test **Pricing Rule Dlits**
2. Create a **Sales Order** with matching items
3. Verify pricing calculations in the console log
4. Check that the correct pricing rule is applied

#### Test Sales Partner Integration
1. Create a **Sales Partner** with auto-create supplier enabled
2. Verify supplier is created automatically
3. Test commission calculations in sales transactions

## Usage Guide

### Creating Pricing Rules

1. **Access Pricing Rule Dlits:**
   - From DLITS Custom workspace → Pricing Rule Dlits
   - Or search "Pricing Rule Dlits" in the awesome bar

2. **Configure Base Price Type:**
   - **Price List Rate**: Uses item's price list rate
   - **Valuation Rate**: Uses item's valuation rate
   - **Selling Rate**: Uses item's selling rate
   - **Item Rate**: Uses direct item rate (no discount needed)

3. **Set Application Criteria:**
   - Choose **Apply On**: Item Code, Item Group, or Brand
   - Select specific items/groups/brands
   - Set date ranges if needed

4. **Configure Discounts:**
   - For Price List/Valuation/Selling Rate: Set discount percentage or amount
   - For Item Rate: No discount configuration required

### Managing Sales Partners

1. **Create Sales Partner:**
   - Go to Sales Partner list
   - Create new partner
   - Enable "Auto Create Supplier" for automatic supplier linking

2. **Commission Management:**
   - Use DLITS Sales Partner Commission Report
   - Track commissions across sales transactions
   - Generate payment entries for commissions

### Using Reports

#### Pricing Rules Analysis
- **Access**: DLITS Custom workspace → Reports section
- **Features**: Filter by date, item, customer
- **Export**: Excel, PDF, CSV formats available

#### DLITS Sales Partner Commission Report
- **Access**: DLITS Custom workspace → Reports section
- **Features**: Commission calculations, payment tracking
- **Actions**: Generate payment entries directly from report

## Troubleshooting

### Common Issues

#### 1. Workspace Not Visible
```bash
# Clear cache and restart
bench --site your-site-name clear-cache
bench restart
```

#### 2. Custom Fields Missing
```bash
# Reinstall custom fields
bench --site your-site-name console
>>> from dlitscustom.fixtures.custom_fields import create_sales_partner_custom_fields
>>> create_sales_partner_custom_fields()
```

#### 3. Pricing Rules Not Working
- Check console logs for pricing rule application messages
- Verify pricing rule criteria match your items
- Ensure pricing rule is enabled and within date range

#### 4. Permission Issues
- Ensure user has appropriate roles
- Check DocType permissions for Pricing Rule Dlits
- Verify workspace permissions

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
# In ERPNext console
import frappe
frappe.conf.developer_mode = 1
frappe.conf.log_level = "DEBUG"
```

## Upgrading

### Standard Upgrade
```bash
cd /path/to/frappe-bench
bench update --app dlitscustom
bench --site your-site-name migrate
bench restart
```

### Manual Migration
```bash
bench --site your-site-name console
>>> from dlitscustom.migrate import execute
>>> execute()
```

## Uninstallation

### Clean Uninstall
```bash
# Uninstall the app
bench --site your-site-name uninstall-app dlitscustom

# Remove app files (optional)
rm -rf apps/dlitscustom
```

### Manual Cleanup
If automatic uninstall fails:

```bash
bench --site your-site-name console
>>> from dlitscustom.uninstall import before_uninstall
>>> before_uninstall()
```

## Development

### File Structure
```
dlitscustom/
├── dlitscustom/
│   ├── doctype/
│   │   └── pricing_rule_dlits/
│   ├── fixtures/
│   │   └── custom_fields.py
│   ├── report/
│   │   ├── pricing_rules_analysis/
│   │   └── sales_partner_commission_report/
│   ├── utils/
│   │   └── get_pricing_rule_dlits.py
│   ├── install.py
│   ├── uninstall.py
│   └── migrate.py
├── hooks.py
└── README.md
```

### Key Files
- **`hooks.py`**: App configuration and event hooks
- **`install.py`**: Installation scripts and setup
- **`uninstall.py`**: Clean removal scripts
- **`migrate.py`**: Version upgrade scripts
- **`get_pricing_rule_dlits.py`**: Core pricing calculation logic

### Contributing
1. Fork the repository
2. Create feature branch
3. Make changes with proper testing
4. Submit pull request

## Support

### Documentation
- ERPNext Documentation: https://docs.erpnext.com
- Frappe Framework: https://frappeframework.com/docs

### Issues
- Report bugs and feature requests through GitHub issues
- Include ERPNext version, error logs, and reproduction steps

### Community
- ERPNext Community Forum
- Frappe Discord Server

## License

This app is licensed under the MIT License. See LICENSE file for details.

## Changelog

### Version 1.0.0
- Initial release
- Pricing Rule Dlits with 4 base price types
- Sales Partner supplier integration
- Comprehensive workspace and reports
- Production-ready installation scripts

---

**Made with ❤️ for the ERPNext community**
