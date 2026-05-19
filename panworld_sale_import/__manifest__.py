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
    "name": "Panworld Sale Import",
    "version": "19.0.1.0.0",
    "category": "Stock",
     "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "account",
        "panworld_sale",
        "scs_import_sale_order",
        "panworld_account"
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/import_data_wizard.xml",
        "wizard/import_sale_order_wizard_views.xml",
        "views/sale_order_view.xml",
        "views/account_move_line_views.xml",
    ],
    "installable": True,
    "application": True,
}
