# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
{
    "name": "Custome Stock Inherite Odoo",
    "version": "19.0.1.0.0",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "summary": "Inherite odoo stock unreserv material from product forercast",
    "description": """
        Inherite odoo stock unreserv material from product forercast
    """,
    "category": "Accounting",
    "depends": [
        "base",
        "stock",
        'web',
    ],
    "data": [
        # "security/ir.model.access.csv",
    ],
    'assets': {
        'web.assets_backend': [
            'custome_stock_inherite/static/src/js/report_stock_forecasted.js',
            ],
    },
    "installable": True,
    "auto_install": False,
    "application": False

}
