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
    'name': 'Sale,Purchase Mass Confirm and Cancel',
    'version': '19.0.1.0.0',
    'category': 'Generic Modules/Others',
    'description': 'Allow To Cancel and Confirm the Sales and Purchase From the Tree View',
    'summary': 'Allow To Cancel and Confirm the Sales and Purchase From the Tree View',
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    'depends': [
        'sale',
        'purchase'
    ],
    'data': [
        'views/sale_view.xml',
        'views/purchase_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
