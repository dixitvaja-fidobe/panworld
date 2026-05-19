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
    "name": "Panworld Stock",
    "summary": "Panworld Stock Customizations",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "depends": [
        "delivery",
        "mrp",
        "purchase_mrp",
        "purchase_stock",
        "stock_picking_back2draft",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/product_template_views.xml",
        "views/stock_location_views.xml",
        "views/stock_move_line_views.xml",
        "views/stock_move_views.xml",
        "views/stock_picking_type_views.xml",
        "views/stock_picking_views.xml",
        "wizard/fs_stock_picking_loc_quant_update_wizard.xml",
        "wizard/fs_stock_quant_xlsx_update_wizard.xml",
        
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
