# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : sales@fidobe.com
#
#############################################################################
{
    'name': "Web Stock Barcode Extra",
    'category': "stock_barcode",
    'version': "19.0.1.0.0",
    'license': 'LGPL-3',
    'description': "Web Stock Barcode Extra - Enhanced barcode scanning with custom fields, manual quantity input, and audio notifications",
    'summary': """Web Stock Barcode Extra - Custom fields display, manual quantity input, save button, and scan counter""",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    'depends': ['web', 'stock_barcode', 'panworld_purchase'],
    'data': [
        'views/stock_picking_type_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'web_stock_barcode_extra/static/src/js/web_stock_barcode_extra.js',
            'web_stock_barcode_extra/static/src/xml/line.xml',
        ],
     },
    'installable': True,
    "auto_install": False,
    'application': True,
}
