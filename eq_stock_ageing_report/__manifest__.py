##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
{
    'name': "Stock Ageing Report",
    'category': 'Inventory',
    "version": "19.0.1.0.0",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    'description': """
        This Module allows you to generate Stock Ageing Report PDF/XLS wise.
        * Allows you to Generate Stock Ageing PDF/XLS Report.
        * Support Multi Warehouse And Multi Locations.
        * Group By Product Category Wise.
        * Filter By Product/Category Wise.
    """,
    'summary': """This Module allows you to generate Stock Ageing Report.
     inventory ageing report | aging report | stock aging report | inventory aging report |
      stock expiry report | inventory expiry report | stock aging report | inventory aging report""",
    'depends': ['base', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'report/report.xml',
        'report/stock_ageing_report.xml',
        'wizard/wizard_stock_ageing_report_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
