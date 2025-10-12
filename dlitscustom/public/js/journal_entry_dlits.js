frappe.ui.form.on('Journal Entry', {
    refresh: function(frm) {
        // console.log('Journal Entry refresh triggered');
        // console.log('Is local:', frm.doc.__islocal);
        // console.log('Commission data:', window.commission_journal_data);
        
        // Check if we have commission journal data stored
        if (window.commission_journal_data && frm.doc.__islocal) {
            let data = window.commission_journal_data;
            // console.log('Setting journal entry data:', data);
            
            // Set accounts after a delay to ensure form is ready
            setTimeout(() => {
                populate_journal_accounts(frm, data);
            }, 1000);
        }
    },
    
    onload: function(frm) {
        // console.log('Journal Entry onload triggered');
        
        // Also try to set data on form load
        if (window.commission_journal_data && frm.doc.__islocal) {
            let data = window.commission_journal_data;
            // console.log('OnLoad: Setting journal data:', data);
            
            // Set accounts after a longer delay
            setTimeout(() => {
                populate_journal_accounts(frm, data);
            }, 1500);
        }
    }
});

function populate_journal_accounts(frm, data) {
    // console.log('Populating journal accounts with data:', data);
    
    try {
        // Clear existing accounts
        frm.clear_table('accounts');
        
        // Set basic Journal Entry fields
        frm.set_value('voucher_type', 'Journal Entry');
        frm.set_value('posting_date', frappe.datetime.get_today());
        
        // Always create account rows immediately for better user experience
        create_account_rows_with_amounts(frm, data);
        
        // Set user remark with commission details
        let user_remark = `Commission accrual for Sales Partner: ${data.sales_partner_name} (${data.sales_partner})`;
        
        if (data.transactions && data.transactions.length > 0) {
            user_remark += '\n\nCommission Details:\n';
            data.transactions.forEach(function(txn) {
                user_remark += `- ${txn.reference_doc} ${txn.reference_name}: ${format_currency(txn.amount)}\n`;
            });
        }
        
        frm.set_value('user_remark', user_remark);
        
        // Try to get default accounts in background
        let company = frappe.defaults.get_default('company');
        // console.log('Company for account lookup:', company);
        // console.log('Supplier for account lookup:', data.linked_supplier);
        
        if (company && data.linked_supplier) {
            // console.log('Making API call to get default accounts...');
            
            frappe.call({
                method: 'dlitscustom.utils.payment_references_dlits.get_default_commission_accounts',
                args: {
                    company: company,
                    supplier: data.linked_supplier
                },
                callback: function(r) {
                    // console.log('Account lookup response:', r);
                    
                    if (r.message) {
                        if (r.message.error) {
                            // console.error('Backend error:', r.message.error);
                            frappe.show_alert({
                                message: __('Could not auto-populate accounts: {0}', [r.message.error]),
                                indicator: 'orange'
                            });
                        } else if (r.message.expense_account || r.message.payable_account) {
                            // Update the account fields with defaults
                            let accounts_table = frm.doc.accounts;
                            // console.log('Current accounts table:', accounts_table);
                            
                            if (accounts_table && accounts_table.length >= 2) {
                                if (r.message.expense_account) {
                                    accounts_table[0].account = r.message.expense_account;
                                    // console.log('Set expense account:', r.message.expense_account);
                                }
                                if (r.message.payable_account) {
                                    accounts_table[1].account = r.message.payable_account;
                                    // console.log('Set payable account:', r.message.payable_account);
                                }
                                
                                frm.refresh_field('accounts');
                                
                                frappe.show_alert({
                                    message: __('Default accounts have been set'),
                                    indicator: 'green'
                                });
                            } else {
                                // console.error('Accounts table not ready:', accounts_table);
                            }
                        } else {
                            // console.log('No accounts found in response');
                            frappe.show_alert({
                                message: __('No default accounts found. Please select accounts manually.'),
                                indicator: 'orange'
                            });
                        }
                    } else {
                        // console.error('No response message');
                    }
                },
                error: function(err) {
                    console.error('API call failed:', err);
                    frappe.show_alert({
                        message: __('Could not fetch default accounts. Please select manually.'),
                        indicator: 'orange'
                    });
                }
            });
        } else {
            // console.log('Missing company or supplier for account lookup');
            frappe.show_alert({
                message: __('Please select accounts manually.'),
                indicator: 'orange'
            });
        }
        
        // console.log('Journal Entry setup completed');
        
        // Show helpful message
        frappe.msgprint({
            title: __('Journal Entry Created'),
            message: __('Commission Journal Entry has been created with amounts and party details. Accounts will be auto-populated if defaults are found.'),
            indicator: 'green'
        });
        
    } catch (error) {
        console.error('Error populating journal accounts:', error);
        frappe.msgprint({
            title: __('Error'),
            message: __('Error setting up Journal Entry: {0}', [error.message]),
            indicator: 'red'
        });
    }
    
    // Clear the stored data after processing
    delete window.commission_journal_data;
}

function create_account_rows_with_amounts(frm, data) {
    // console.log('Creating account rows with amounts');
    
    // Create debit entry (Commission Expense)
    let debit_row = frm.add_child('accounts');
    debit_row.account = ''; // Will be filled by user or default lookup
    debit_row.debit_in_account_currency = data.total_amount;
    debit_row.credit_in_account_currency = 0;
    debit_row.user_remark = `Commission expense for ${data.sales_partner_name}`;
    
    // Create credit entry (Accounts Payable to Supplier)
    let credit_row = frm.add_child('accounts');
    credit_row.account = ''; // Will be filled by user or default lookup
    credit_row.party_type = 'Supplier';
    credit_row.party = data.linked_supplier;
    credit_row.debit_in_account_currency = 0;
    credit_row.credit_in_account_currency = data.total_amount;
    credit_row.user_remark = `Commission payable to ${data.linked_supplier}`;
    
    // Refresh the accounts table
    frm.refresh_field('accounts');
    
    // console.log('Account rows created successfully');
}
