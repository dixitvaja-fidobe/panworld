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
    "name": "Panworld Expense",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "summary": "Panworld Expence Scope and Customizations",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "data": [
        "data/ir_sequence_data.xml",
        "views/expence_view.xml",
        "views/account_views.xml",
    ],
    "depends": [
        "hr_expense",
        "account",
        "panworld_contact",
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
