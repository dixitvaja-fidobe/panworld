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
    "name": "Account Move Number Sequence",
    "version": "19.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "summary": "Generate journal entry number from sequence",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "account",
    ],
    "demo": [
        "demo/ir_sequence_demo.xml",
        "demo/account_journal_demo.xml",
    ],
    "data": [
        "views/account_journal_views.xml",
        "views/account_move_views.xml",
        "security/ir.model.access.csv",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
