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
    "name": "Stock Picking Invoice Link",
    "version": "19.0.1.0.0",
    "category": "Warehouse Management",
    "summary": "Adds link between pickings and invoices",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "stock",
        "stock_account",
    ],
    "data": [
        "views/stock_view.xml",
        "views/account_invoice_view.xml"
    ],
    "installable": True,
    "auto_install": False,
    "application": False

}
