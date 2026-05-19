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
    'name': "PO Compare Cancel Line",
    'version': '19.0.1.0.0',
    'summary': """PO compare line and cancel line""",
    'description': """PO compare line and cancel line""",
    'category': 'purchase',
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    'depends': [
        'base',
        'purchase',
        "account"
    ],
    'data': [
        'security/security.xml',
        "data/merge_bill_action.xml",
        'views/purchase_order_view.xml',
        "views/purchase_order_line_view.xml"
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
