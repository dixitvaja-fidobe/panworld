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
    "name": "Panworld Import",
    "version": "19.0.1.0.0",
    "category": "Stock",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "stock",
        "panworld_purchase",
        "panworld_landed_cost"
    ],
    "data": [
        # "data/res.users.csv",
        # "data/product.category.csv",
        # "data/account.account.csv",
        # "data/product.template.csv",
        # "data/account.payment.term.csv",
        # "data/res.partner.csv",
        "security/ir.model.access.csv",
        "wizard/import_data_wizard.xml",
        "views/stock_picking_view.xml",
        "views/purchase_order_view.xml",
        "views/purchase_request_view.xml",
        "views/rma_return_view.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
