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
    "name": "Report Layout",
    "version": "19.0.1.0.0",
    "category": "customisation",
    "summary": "Custom report layout, designed for panworld",
    "description": "Custom report layout, designed for panworld",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        # "panworld_purchase"
    ],
    "data": [
        "views/report_templates.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "panworld_report_layout/static/src/scss/layout_standard.scss",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": False
}
