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
    "name": "Costing Reports",
    "version": "19.0.1.0.0",
    "category": "Products",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        'sale',
        'account',
        'product',
        "panworld_contact",
        "scs_rma"
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/view_account_journal.xml",
        "views/view_costing_report.xml",
        "views/view_tracking_number.xml",
        "views/view_account_move.xml",
        "views/view_product_inherit.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False

}
