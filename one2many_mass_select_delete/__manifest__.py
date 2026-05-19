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
    'name': 'One2many Mass Select Delete Widget',
    'version': "19.0.1.0.0",
    'category': 'Extra Tools',
    'summary': """One2many Mass Delete Select/Deselect Widget""",
    'description': """With this module, you can delete multiple lines in the
    one2many field that is selected or unselected""",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    'depends': ['web', 'base'],
    'assets': {
        'web.assets_backend': [
            'one2many_mass_select_delete/static/src/css/widget.css',
            'one2many_mass_select_delete/static/src/xml/one2many_delete_templates.xml',
            'one2many_mass_select_delete/static/src/js/list_renderer.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
