// ── Dialog helpers (standalone, not inside form event) ──────────────────────

function _show_approve_dialog(frm) {
    var d = new frappe.ui.Dialog({
        title: "Approve Commission",
        fields: [
            {
                fieldname: "deduction_approved",
                label: "Deduction Amount",
                fieldtype: "Currency",
                default: frm.doc.deduction_approved || 0,
                description: "Enter 0 to pay the full commission. Enter the amount to deduct if a return occurred."
            },
            {
                fieldname: "remarks",
                label: "Remarks",
                fieldtype: "Small Text"
            }
        ],
        primary_action_label: "Approve",
        primary_action: function(values) {
            frappe.call({
                method: "dlitscustom.dlitscustom.doctype.dlits_invoice_commission.dlits_invoice_commission.approve_invoice_commission",
                args: {
                    name: frm.doc.name,
                    deduction: values.deduction_approved || 0,
                    remarks: values.remarks || ""
                },
                callback: function(r) {
                    d.hide();
                    frm.reload_doc();
                    frappe.show_alert({ message: "Commission approved.", indicator: "green" });
                }
            });
        }
    });
    d.show();
}

function _show_update_deduction_dialog(frm) {
    var d = new frappe.ui.Dialog({
        title: "Update Deduction",
        fields: [
            {
                fieldname: "deduction_approved",
                label: "New Deduction Amount",
                fieldtype: "Currency",
                default: frm.doc.deduction_approved || 0
            },
            {
                fieldname: "remarks",
                label: "Remarks",
                fieldtype: "Small Text",
                reqd: 1
            }
        ],
        primary_action_label: "Update",
        primary_action: function(values) {
            frappe.call({
                method: "dlitscustom.dlitscustom.doctype.dlits_invoice_commission.dlits_invoice_commission.update_deduction",
                args: {
                    name: frm.doc.name,
                    deduction: values.deduction_approved || 0,
                    remarks: values.remarks || ""
                },
                callback: function(r) {
                    d.hide();
                    frm.reload_doc();
                }
            });
        }
    });
    d.show();
}

function _show_additional_salary_dialog(frm, employee) {
    var d = new frappe.ui.Dialog({
        title: "Record Payment — Additional Salary",
        fields: [
            {
                fieldname: "employee",
                label: "Employee",
                fieldtype: "Link",
                options: "Employee",
                default: employee,
                reqd: 1
            },
            {
                fieldname: "salary_component",
                label: "Salary Component",
                fieldtype: "Link",
                options: "Salary Component",
                default: "Sales Commission",
                reqd: 1
            },
            {
                fieldname: "payroll_date",
                label: "Payroll Date",
                fieldtype: "Date",
                default: frappe.datetime.get_today(),
                reqd: 1
            },
            {
                fieldname: "amount",
                label: "Amount",
                fieldtype: "Currency",
                default: frm.doc.balance,
                reqd: 1
            }
        ],
        primary_action_label: "Create & Submit",
        primary_action: function(values) {
            frappe.call({
                method: "dlitscustom.dlitscustom.doctype.dlits_invoice_commission.dlits_invoice_commission.create_payment_additional_salary",
                args: {
                    name: frm.doc.name,
                    employee: values.employee,
                    salary_component: values.salary_component,
                    payroll_date: values.payroll_date,
                    amount: values.amount
                },
                callback: function(r) {
                    d.hide();
                    frm.reload_doc();
                    frappe.show_alert({ message: "Payment recorded via Additional Salary.", indicator: "green" });
                }
            });
        }
    });
    d.show();
}

function _show_je_dialog(frm) {
    var d = new frappe.ui.Dialog({
        title: "Record Payment — Journal Entry",
        fields: [
            {
                fieldname: "payment_date",
                label: "Payment Date",
                fieldtype: "Date",
                default: frappe.datetime.get_today(),
                reqd: 1
            },
            {
                fieldname: "expense_account",
                label: "Commission Expense Account",
                fieldtype: "Link",
                options: "Account",
                filters: { root_type: "Expense" },
                reqd: 1
            },
            {
                fieldname: "payment_account",
                label: "Payment Account (Bank/Cash)",
                fieldtype: "Link",
                options: "Account",
                filters: { account_type: ["in", ["Bank", "Cash"]] },
                reqd: 1
            },
            {
                fieldname: "amount",
                label: "Amount",
                fieldtype: "Currency",
                default: frm.doc.balance,
                reqd: 1
            },
            {
                fieldname: "cheque_no",
                label: "Cheque / Transfer No.",
                fieldtype: "Data"
            }
        ],
        primary_action_label: "Create & Submit",
        primary_action: function(values) {
            frappe.call({
                method: "dlitscustom.dlitscustom.doctype.dlits_invoice_commission.dlits_invoice_commission.create_payment_journal_entry",
                args: {
                    name: frm.doc.name,
                    payment_date: values.payment_date,
                    expense_account: values.expense_account,
                    payment_account: values.payment_account,
                    amount: values.amount,
                    cheque_no: values.cheque_no || null
                },
                callback: function(r) {
                    d.hide();
                    frm.reload_doc();
                    frappe.show_alert({ message: "Payment recorded via Journal Entry.", indicator: "green" });
                }
            });
        }
    });
    d.show();
}

function _show_payment_method_dialog(frm, employee) {
    var d = new frappe.ui.Dialog({
        title: "Select Payment Method",
        fields: [
            {
                fieldname: "method",
                label: "Payment Method",
                fieldtype: "Select",
                options: "Additional Salary (Payroll)\nJournal Entry (Direct Bank Transfer)",
                default: "Additional Salary (Payroll)"
            }
        ],
        primary_action_label: "Next",
        primary_action: function(values) {
            d.hide();
            if (values.method === "Additional Salary (Payroll)") {
                _show_additional_salary_dialog(frm, employee);
            } else {
                _show_je_dialog(frm);
            }
        }
    });
    d.show();
}

// ── Form events ─────────────────────────────────────────────────────────────

frappe.ui.form.on("Dlits Invoice Commission", {

    refresh: function(frm) {
        var has_approver = frappe.user.has_role("Shb Commission Approver");
        var has_accounts = frappe.user.has_role("Accounts Manager");
        var status = frm.doc.status;

        // Approve button
        if (has_approver && ["Pending", "Under Review"].includes(status)) {
            frm.add_custom_button("Approve Commission", function() {
                _show_approve_dialog(frm);
            }, "Actions").addClass("btn-success");
        }

        // Update Deduction button (after approval if returns happen later)
        if (has_approver && ["Approved", "Partially Paid"].includes(status)) {
            frm.add_custom_button("Update Deduction", function() {
                _show_update_deduction_dialog(frm);
            }, "Actions");
        }

        // Record Payment button
        if ((has_approver || has_accounts) && ["Approved", "Partially Paid"].includes(status) && frm.doc.balance > 0) {
            frm.add_custom_button("Record Payment", function() {
                frappe.call({
                    method: "dlitscustom.dlitscustom.doctype.dlits_invoice_commission.dlits_invoice_commission.get_invoice_commission_partner_info",
                    args: { name: frm.doc.name },
                    callback: function(r) {
                        var info = r.message || {};
                        if (info.partner_type === "Internal User" && info.employee) {
                            _show_payment_method_dialog(frm, info.employee);
                        } else {
                            _show_je_dialog(frm);
                        }
                    }
                });
            }, "Actions").addClass("btn-primary");
        }

        // Close button
        if (has_approver && ["Paid", "Approved", "Partially Paid"].includes(status)) {
            frm.add_custom_button("Close Commission", function() {
                frappe.prompt(
                    { fieldname: "remarks", label: "Closing Remarks", fieldtype: "Small Text" },
                    function(values) {
                        frappe.call({
                            method: "dlitscustom.dlitscustom.doctype.dlits_invoice_commission.dlits_invoice_commission.close_commission",
                            args: { name: frm.doc.name, remarks: values.remarks || "" },
                            callback: function() { frm.reload_doc(); }
                        });
                    },
                    "Close Commission", "Close"
                );
            }, "Actions");
        }

        // Needs review badge
        if (frm.doc.needs_review) {
            frm.dashboard.set_headline(
                '<span style="color:orange;font-weight:bold;">⚠ Sales return detected — commission needs manager review before payment.</span>'
            );
        }

        // Colour-code status indicator
        var colour_map = {
            "Pending": "orange",
            "Under Review": "red",
            "Approved": "blue",
            "Partially Paid": "purple",
            "Paid": "green",
            "Closed": "darkgrey"
        };
        if (colour_map[status]) {
            frm.page.set_indicator(status, colour_map[status]);
        }
    }
});
