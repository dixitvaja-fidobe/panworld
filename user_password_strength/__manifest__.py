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
    'name': "User Password Strength - Restrict Weak Password",
    'version': "19.0.1.0.0",
    'summary': """ User password strength - restrict weak password""",
    'description': """ Customized setting to restrict weak password which is 
     completely configurable. Also, allows the preset password strength checkup
      while resetting.""",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    'category': 'Tools',
    'depends': ['base',
                'website'],
    'data': [
        'views/signup_page_view.xml',
        'views/restrict_password.xml',
    ],
    'assets': {
            'web.assets_frontend': ['user_password_strength/static/src/js/signup_user.js', ],
    },
    'installable': True,
    'auto_install': True,
    'application': False
}
