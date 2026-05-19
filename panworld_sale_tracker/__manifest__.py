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
    "name": "Panworld Sale Tracker",
    "version": "19.0.1.0.0",
    "category": "sale",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "panworld_sale",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/mail_template_sale_tracker_tat_breach.xml",
        "data/sale_tracker_mail_cron.xml",
        "views/sale_tracker_view.xml",
        "views/res_company_views.xml"
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
