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
    "name": "Invoice From Picking(Shipment/Delivery Order) Odoo inherit",
    "version": "19.0.1.0.0",
    "summary": "customer invoice from picking vendor invoices from Picking customer "
               "invoice from delivery order vendor bill from picking vendor bill from "
               "receipt invoice from Shipment invoice from Shipment Account invoice "
               "from picking single invoice from delivery order",
    "description": """invoice_from_picking inherite module""",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "base",
        "invoice_from_picking",
    ],
    "data": [
    ],
    "auto_install": False,
    "installable": True,
    "license": "OPL-1",
}
