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
    'name': "Account Partner Ledger Report",
    'description': """Account Partner Ledger Report""",
    "version": "19.0.1.0.0",
    "summary": "Account Aged Report Extended",
    "category": "Accounting",
    'author': "Jumana | Fidobe Solutions",
    "website": "www.fidobe.com",
    'depends': ['base', 'account', 'account_reports'],
    'data': [
        'data/account_partner_ledger_report.xml',
    ],
    "installable": True,
    "auto_install": False,
    "license": "OPL-1",
}
