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
    'name': 'Panworld POS',
    'version': '19.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Customizations for Panworld POS',
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    'description': """
        This module includes custom logic for Panworld POS.
        - Auto select invoice option in POS.
        - Prevent negative stock based on POS Operation Type setting.
    """,
    'depends': ['point_of_sale', 'pos_sale'],
    'data': [
        'views/stock_picking_type_view.xml',
        'views/pos_order_view.xml',
        'views/res_config_settings.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'panworld_pos/static/src/app/components/product_card/product_card.css',
            'panworld_pos/static/src/app/**/*',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
