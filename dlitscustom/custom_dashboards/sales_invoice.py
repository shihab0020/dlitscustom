from frappe import _

def get_data(data=None):
    return {
        'fieldname': 'reference_name',
        'non_standard_fieldnames': {
            'Dlits Customer Followup': 'reference_name'
        },
        'transactions': [
            {
                'label': _('Related'),
                'items': ['Payment Entry', 'Delivery Note', 'Dlits Customer Followup']
            }
        ]
    }