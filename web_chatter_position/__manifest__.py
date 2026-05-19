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
    "name": "Chatter Position",
    "summary": "Add an option to change the chatter position",
    "version": "19.0.1.0.0",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "category": "Extra Tools",
    "depends": ["web", "mail"],
    "data": [
        "views/res_users.xml",
        "views/web.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "/web_chatter_position/static/src/**/*.js",
            "/web_chatter_position/static/src/**/*.scss",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": False
}
