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
    'name': 'Bill Lines Update',
    "version": "19.0.1.0.0",
    'summary': 'Bill Lines Update',
    'description': 'Bill Lines Update',
    'category': 'Accounting',
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    'depends': [
        'account',
        'purchase',
        'panworld_import'
    ],
    'data': [
        'security/user_groups.xml',
        'views/bill.xml',
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
