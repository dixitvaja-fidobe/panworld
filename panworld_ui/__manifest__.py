# -*- coding: utf-8 -*-
{
    'name': 'Panworld UI',
    'version': '1.0',
    'category': 'User Interface',
    'summary': 'Enhanced UI components for Panworld, including 5-star priority widget.',
    'description': """
        This module provides UI enhancements:
        - Upgrades the priority widget to 5 stars for CRM Leads and Project Tasks.
        - Adds a 5-star priority field to Sale and Purchase Orders.
        - Custom premium styling for the priority widget.
    """,
    'author': 'Panworld',
    'depends': ['base', 'sale', 'purchase', 'crm', 'project'],
    'assets': {
        'web.assets_backend': [
            'panworld_ui/static/src/scss/priority_custom.scss',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
