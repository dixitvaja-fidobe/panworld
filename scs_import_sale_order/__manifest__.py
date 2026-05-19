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
    "name": "SCS Import Sale Order from excel file",
    "version": "19.0.1.0.0",
    "category": "Sales",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "sale_management"
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order_views.xml",
        "views/account_move_view.xml",
        "wizard/import_sale_order_wizard_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
