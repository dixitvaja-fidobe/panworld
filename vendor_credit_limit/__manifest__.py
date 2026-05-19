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
    "name": "Vendor Credit Limit",
    "version": "19.0.1.0.0",
    "category": "Purchase",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "data": [],
    "depends": [
        "purchase",
        "panworld_purchase"
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
        "wizard/purchase_confirmation_view.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}

