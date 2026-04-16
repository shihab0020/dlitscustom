from frappe import _

def get_data(data=None):
    return {
        'fieldname': 'customer',
        'non_standard_fieldnames': {
            'Opportunity': 'party_name',
            'Quotation': 'party_name'
        },
        'transactions': [
            {
                'label': _('Pre Sales'),
                'items': ['Opportunity', 'Quotation']
            },
            {
                'label': _('Sales'),
                'items': ['Sales Order', 'Delivery Note', 'Sales Invoice']
            },
            {
                'label': _('Follow-ups'),
                'items': ['Dlits Customer Followup']
            },
            {
                'label': _('Support'),
                'items': ['Issue']
            }
        ]
    }