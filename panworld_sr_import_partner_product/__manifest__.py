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
    "name": "Import Products",
    "version": "19.0.1.0.0",
    "summary": "This module helps you to import products",
    "category": "Accounting",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "sale",
        "stock",
        "product"
    ],
    "data": [
        "security/ir.model.access.csv",
         "wizard/sr_import_product.xml"
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
