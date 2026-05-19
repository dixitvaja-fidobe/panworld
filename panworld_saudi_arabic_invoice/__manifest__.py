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
    "name": "Panworld Saudi Arabia - Invoice",
    "version": "19.0.1.0.0",
    "category": "account",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "account",
        "costing_reports",
    ],
    "data": [
        "views/view_panworld_saudi_arabic_move_form.xml",
        "views/res_company_view.xml",
        "report/report_templates.xml",
        # "report/panworld_saudi_arabic_invoice_templates.xml",
        # "report/panworld_saudi_arabic_invoice_report.xml",
        "report/sa_invoice_templates.xml",
        "report/sa_invoice_report.xml",
        "report/sa_quotation_templates.xml",
        "report/sa_quotation_report.xml"
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
