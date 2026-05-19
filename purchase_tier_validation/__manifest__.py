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
    "name": "Purchase Tier Validation",
    "summary": "Extends the functionality of Purchase Orders to "
                "support a tier validation process.",
    "version": "19.0.1.0.0",
    "category": "Purchases",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "purchase",
        "base_tier_validation"
    ],
    "data": [
        "views/purchase_order_view.xml"
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
