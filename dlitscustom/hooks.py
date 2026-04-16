from . import __version__ as app_version

app_name = "dlitscustom"
app_title = "dlitscustom"
app_publisher = "shihab"
app_description = "Custom Modification For Dlits"
app_email = "shihab@dlits-sa.com"
app_license = "mit"

# Includes in <head>
# ------------------
# Add to hooks.py
# app_include_css = "/assets/dlitscustom/css/dlits_customer_followup.css"
# include js, css files in header of desk.html
# app_include_css = "/assets/dlitscustom/css/dlitscustom.css"
# app_include_js = "/assets/dlitscustom/js/chartjs-plugin-datalabels.min.js"

# include js, css files in header of web template
# web_include_css = "/assets/dlitscustom/css/dlitscustom.css"
# web_include_js = "/assets/dlitscustom/js/dlitscustom.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "dlitscustom/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Quotation": "public/js/quotation_pricing_rule_dlits.js",
    "Sales Order": "public/js/sales_order_pricing_rule_dlits.js",
    "Sales Invoice": "public/js/sales_invoice_pricing_rule_dlits.js",
    "Payment Entry": "public/js/payment_entry_dlits.js",
    "Journal Entry": "public/js/journal_entry_dlits.js",
    "Customer": "public/js/customer.js",
    "Quotation": "public/js/quotation.js"
}

# Customer Followup related document events
# doctype_js = {
#     "Dlits Customer Followup": "public/js/dlits_customer_followup.js",
#     "Customer": "public/js/customer.js"
# }
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "dlitscustom/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "dlitscustom.utils.jinja_methods",
# 	"filters": "dlitscustom.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "dlitscustom.install.before_install"
after_install = "dlitscustom.install.after_install"

# Uninstallation
# ------------

before_uninstall = "dlitscustom.install.before_uninstall"
# after_uninstall = "dlitscustom.install.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "dlitscustom.utils.before_app_install"
# after_app_install = "dlitscustom.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "dlitscustom.utils.before_app_uninstall"
# after_app_uninstall = "dlitscustom.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "dlitscustom.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Sales Invoice": {
        "validate": [
            "dlitscustom.override.pricing_rule_verify_dlits.pricing_rule_verify_dlits",
            "dlitscustom.override.sales_invoice_commission.validate_sales_invoice_commission"
        ],
        "on_submit": "dlitscustom.override.sales_invoice_commission.on_submit_sales_invoice_commission",
        "on_cancel": "dlitscustom.override.sales_invoice_commission.on_cancel_sales_invoice_commission"
    },
    "Sales Order": {
        "validate": [
            "dlitscustom.override.pricing_rule_verify_dlits.pricing_rule_verify_dlits",
            "dlitscustom.override.sales_order_commission.validate_sales_order_commission"
        ]
    },
    "Quotation": {
        "validate": "dlitscustom.override.pricing_rule_verify_dlits.pricing_rule_verify_dlits"
    }
    # "Customer": {
    #     "on_update": "dlitscustom.dlitscustom.doctype.dlits_customer_followup.dlits_customer_followup.update_customer_aging"
    # }
}

fixtures = [
    {"doctype": "Property Setter"},
    {"doctype": "DocType", "filters": [["name", "in", ["Pricing Rule Item Code Dlits Test"]]]},
    {
        "dt": "Custom Field",
        "filters": [
            ["dt", "=", "Customer"],
            ["fieldname", "in", [
                "custom_last_followup_status", 
                "custom_last_followup_date", 
                "custom_followup_aging"
            ]]
        ]
    }
]

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"dlitscustom.tasks.all"
# 	],
# 	"daily": [
# 		"dlitscustom.tasks.daily"
# 	],
# 	"hourly": [
# 		"dlitscustom.tasks.hourly"
# 	],
# 	"weekly": [
# 		"dlitscustom.tasks.weekly"
# 	],
# 	"monthly": [
# 		"dlitscustom.tasks.monthly"
# 	],
# }

# Scheduled Tasks for customer followup aging and reminders
scheduler_events = {
    "daily": [
        "dlitscustom.dlitscustom.doctype.dlits_customer_followup.dlits_customer_followup.update_customer_aging",
        "dlitscustom.dlitscustom.doctype.dlits_customer_followup.dlits_customer_followup.send_followup_reminders"
    ]
}
# Testing
# -------

# before_tests = "dlitscustom.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "dlitscustom.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "dlitscustom.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["dlitscustom.utils.before_request"]
# after_request = ["dlitscustom.utils.after_request"]

# Job Events
# ----------
# before_job = ["dlitscustom.utils.before_job"]
# after_job = ["dlitscustom.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Reports
# -------

# reports = [
#     {
#         "doctype": "Report",
#         "name": "DLITS Sales Analytics",
#         "module": "dlitscustom",
#         "category": "Sales"
#     }
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"dlitscustom.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }