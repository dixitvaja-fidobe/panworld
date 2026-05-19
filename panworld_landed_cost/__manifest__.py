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
    "name": "Panworld Landed Cost",
    "version": "19.0.1.0.0",
    "category": "Purchase",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "purchase_stock",
        "stock_landed_costs",
        "stock_delivery",
        "panworld_uk_warehouse",
        "panworld_purchase",
        "costing_reports"
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/stock_landed_cost_data.xml",
        "views/stock_picking_views.xml",
        "views/stock_landed_cost.xml",
        "views/purchase_order_views.xml",
        "views/account_payment_views.xml",
        "wizard/choose_delivery_carrier_views.xml",
        "wizard/landed_cost_batch_payment_view.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
