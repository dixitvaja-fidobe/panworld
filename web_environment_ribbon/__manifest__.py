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
    "name": "Web Environment Ribbon",
    "version": "19.0.1.0.3",
    "category": "Web",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": ["web"],
    "data": [
        "data/ribbon_data.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "web_environment_ribbon/static/src/components/environment_ribbon/*",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": False
}
