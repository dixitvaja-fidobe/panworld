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
    'name': 'Pos Stock Info',
    'version': '19.0.1.0.0',
    'category': 'Point Of Sale',
    'description': "Pos Stock Info",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    'data': [
        "views/pos_session_view.xml"
    ],
    'depends': [
        'point_of_sale',
    ],
    'assets': {
         'web.assets_qweb': [
             'pos_stock_info/static/src/xml/pos_stock_info.xml',
         ],
     },
    "installable": True,
    "auto_install": False,
    "application": False
}
