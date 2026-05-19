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
    "name": "Product Search Multi Value",
    "version": "19.0.1.0.0",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "product",
        "sale",
        # "panworld_purchase",
        "purchase",
        "account"
    ],
    "data": [
        "data/search_field_data.xml",
        "views/product_template_view.xml"
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
