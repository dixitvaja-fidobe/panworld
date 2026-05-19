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
    "name": "Custome email Marketing",
    "version": "19.0.1.0.0",
    "category": "Email Marketing",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    'depends': [
        'mass_mailing',
    ],
    "data": [
         "views/email_contact.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
