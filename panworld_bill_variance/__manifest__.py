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
    "name": "Panworld Bill Variance",
    "version": "19.0.1.0.0",
    "category": "Purchase",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "account",
        "product"
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/product_template.xml",
        "wizard/bill_variance_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
