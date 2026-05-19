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
    'name': 'Payroll Send Email - Batch Payslips',
    'version': '19.0.1.0.0',
    'summary': 'Payroll Send Email - Batch Payslips',
    'description': 'Payroll Send Email - Batch Payslips',
    'category': 'HR',
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    'depends': ['hr_payroll'],
    'data': [
        "security/ir.model.access.csv",
        'report/payslip_ext.xml',
        'data/mail_template_data.xml',
        "wizard/payslips_employee_wizard_view.xml",
        'views/hr_payslip_run_inherit.xml',
        'views/hr_payslip_inherit.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
