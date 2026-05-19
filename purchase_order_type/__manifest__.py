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
    "name": "Purchase Order Type",
    "version": "19.0.1.0.0",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "category": "Purchase Management",
    "depends": [
        "purchase"
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/view_purchase_order_type.xml",
        "views/view_purchase_order.xml",
        "views/res_partner_view.xml",
        "data/purchase_order_type.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
