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
    'name': 'Product Control Policy',
    'summary': 'Update Products Control Policy to Order Qty',
    'author': 'Mariam Shahin',
    'website': 'https://www.plennix.com/',
    'version': '19.0.1.0.0',
    'category': 'Purchase',
    'license': 'OPL-1',
    'depends': [
        'purchase',
    ],
    'data': [
        'data/actions.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
