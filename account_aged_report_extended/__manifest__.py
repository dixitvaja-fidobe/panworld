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
    "name": "Account Aged Report Extend",
    "version": "19.0.1.0.0",
    "description": """ Account Aged Report Extended """,
    "summary": "Account Aged Report Extended",
    "category": "Accounting",
    'author': "Jumana | Fidobe Solutions",
    "website": "www.fidobe.com",
    "depends": ['account_reports'],
    "data": [
        'data/account_aged_partner_balance_report.xml',
    ],
    "assets": {
        'web.assets_backend': [
            'account_aged_report_extended/static/src/js/account_report.js',
        ],
    },
    "installable": True,
    "auto_install": False,
    "license": "OPL-1",
}
