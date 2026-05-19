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
    "name": "Panworld Product Management",
    "version": "19.0.1.0.0",
    'summary': 'Panworld Products Management',
    'description': 'Panworld Products Management',
    "category": "Products",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "product",
        "stock",
        "purchase",
        "product_dimension",
        "panworld_contact"
    ],
    "data": [
        "security/ir.model.access.csv",
         "views/product_sub_categ.xml",
         "views/product_template_view.xml",
         "views/product_view.xml"
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
