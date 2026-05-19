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
    'name': 'Panworld Payroll',
    'version': '19.0.1.0.0',
    'summary': 'Panworld Payroll',
    'description': 'Panworld Payroll',
    'category': 'HR',
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    'depends': [
        'hr_payroll'
    ],
    'data': [
        'report/payslip_ext.xml',
        'views/hr_payslip.xml',
        # 'views/hr_contract.xml',
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}