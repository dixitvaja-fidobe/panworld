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
    'name': 'So Compare Cancel Line',
    'version': '19.0.1.0.0',
    'summary': 'SO Compare Line and Cancel Line',
    'description': 'SO Compare Line and Cancel Line',
    'category': 'Sales',
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    'depends': [
        'base',
        'sale'
    ],
    'data': [
        'security/security.xml',
        'views/sale_order_view.xml',
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
