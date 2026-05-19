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
    "name": "Panworld Contact",
    "summary":"Panworld Contact",
    "version": "19.0.1.0.0",
    "category": "Purchase",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "contacts",
        "hr",
        "sale"
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/res_partner_category.xml",
        "data/division_type_data.xml",
        "data/ir_sequence_data.xml",
        "data/server_actions.xml",
        "views/res_partner_views.xml",
        "views/division_type_view.xml"
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
