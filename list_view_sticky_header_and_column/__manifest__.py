# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
{
    'name': "Sticky Header And Column In List View",
    'version': '19.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Enhance list views with sticky headers and columns for 
    improved navigation and readability.""",
    'description': """This module enhances Odoo list views by introducing sticky
     headers and columns. When scrolling through long lists, the header and 
     selected columns remain visible, providing context and easy access to 
     column information. Users can interact with data more effectively without 
     losing track of column titles.""",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    'depends': ['account', 'purchase', 'hr_expense', 'web'],
    'assets': {
        'web.assets_backend': [
            ('after', 'web/static/src/views/list/list_renderer.xml',
             'list_view_sticky_header_and_column/static/src/**/*'),
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
