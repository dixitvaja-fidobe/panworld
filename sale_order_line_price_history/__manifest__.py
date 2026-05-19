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
    "name": "Sale order line price history",
    "version": "19.0.1.0.0",
    "category": "Sales Management",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": ["sale"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/sale_order_line_price_history.xml",
        "views/sale_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "sale_order_line_price_history/static/src/js/*.js",
            "sale_order_line_price_history/static/src/xml/*.xml",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": False
}
