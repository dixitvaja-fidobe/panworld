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
    'name': 'SMTP BY USERS AND COMPANIES',
    'description': """Customised module which allows to configure
     outgoing email server by users and companies.""",
    'summary': """Configure different outgoing mail server for multiple companies and multiple users.""",
    'version': '19.0.1.0.0',
    'category': 'Mail',
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    'depends': ['mail'],
    'data': [
        'views/res_config_views.xml',
        'views/ir_mail_server_view.xml',
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
