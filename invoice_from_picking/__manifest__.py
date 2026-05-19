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
    "name": "Invoice From Picking(Shipment/Delivery Order) Odoo",
    "version": "19.0.1.0.0",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "base",
        "account",
        "sale_management",
        "stock",
        "purchase",
        "sale_stock",
        "panworld_account",
        "stock_picking_invoice_link"
    ],
    "category": "Accounting",
    "data": [
        "security/ir.model.access.csv",
        "data/cron_vendor_bill_update.xml",
        "wizard/stock_invoice_onshipping.xml",
        "views/inherited_stock_picking.xml",
        "views/inherited_invoice_view.xml",
        "views/inherited_purchase.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}

