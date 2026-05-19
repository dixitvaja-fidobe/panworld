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
    "name": "Pickings back to draft",
    "summary": "Reopen canceled transfers",
    "version": "19.0.1.0.0",
    "category": "Warehouse Management",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "stock"
    ],
    "data": [
        "views/picking_view.xml"
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
