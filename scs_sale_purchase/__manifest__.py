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
    "name": "Auto Purchase from Sales",
    "version": "19.0.1.0.0",
    "category": "Sales Management",
    "summary": """Create PO from SO for single or multiple vendors.""",
    'category': 'purchase',
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "sale_purchase"
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizards/wiz_sale_purchase_order.xml",
        "views/sale_order_views.xml",
        "views/purchase_order_views.xml"
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
