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
    "name": "Panworld History Management",
    "version": "19.0.1.0.0",
    "category": "Products",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": ["product", "sale",
                "account", "purchase",
                'stock', 'mail',
                'panworld_purchase',
                'panworld_landed_cost',
                'so_compare_cancel_line'],
    "data": [
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/history_model_view.xml",
        "views/history_report.xml"

    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
