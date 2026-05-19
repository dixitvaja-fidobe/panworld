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
    "name": "Search on One2many",
    "version": "19.0.1.0.0",
    "category": "custom",
    "description": "search option on one2many and many2many relational field",
    "summary": """Search option helps to search record from one2many and many2many field.""",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "base",
        "purchase",
        "sale",
        "sale_management",
        "account"
    ],
    "data": [
        'views/form_view_inherits.xml'
    ],

    'assets': {
        'web.assets_backend': [
            'ps_search_one2many_many2many/static/src/css/relational_field.css',
            'ps_search_one2many_many2many/static/src/js/relational_field.js',
            'ps_search_one2many_many2many/static/src/xml/relational_field.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
