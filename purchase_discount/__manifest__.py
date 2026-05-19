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
    "name": "Purchase Order Line Discount",
    "summary": "Purchase Order Line Discount",
    "category": "Purchase Management",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "depends": [
        "purchase"
    ],
    "data": [
        "views/purchase_discount_view.xml",
        "views/product_supplierinfo_view.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
