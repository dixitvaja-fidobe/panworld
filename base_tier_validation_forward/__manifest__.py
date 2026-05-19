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
    "name": "Base Tier Validation Forward",
    "summary": "Forward option for base tiers",
    "version": "19.0.1.0.0",
    "category": "Tools",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "base_tier_validation"
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/mail_data.xml",
        "views/tier_definition_view.xml",
        "wizard/forward_wizard_view.xml",
        "templates/tier_validation_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "base_tier_validation_forward/static/src/xml/tier_review_template.xml",
        ],
    },
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "auto_install": False,
    "application": False
}
