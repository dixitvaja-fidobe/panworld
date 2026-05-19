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
    'name': "Inventory Valuation Report",
    'category': 'Stock',
    "version": "19.0.1.0.0",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    'description': """
        This Module allows you to generate Inventory Valuation Report PDF/XLS wise.
    """,
    'summary': """Inventory Report | Valuation Report | Real Time Valuation Report 
    | Real Time Stock Report | Stock Report | Stock card | Stock Valuation Report | 
    Odoo Inventory Report | stock card report | stock card valuation report | stock balance""",
    'depends': ['base', 'stock_account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/wizard_inventory_valuation_view.xml',
        'report/report.xml',
        'report/inventory_valuation_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
