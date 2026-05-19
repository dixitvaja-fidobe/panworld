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
    "name": "Panworld Uk Warehouse",
    "summary": "Panworld Uk Warehouse",
    "version": "19.0.1.0.0",
    "category": "Purchase",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        'base',
        'product',
        'stock'
    ],
    "data": [
        "security/security.xml",
        "views/uk_warehouse_stock_quant_views.xml"
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
