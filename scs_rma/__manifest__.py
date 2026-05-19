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
    "name": "RMA-Return Merchandise Authorization Return Exchange Management",
    "version": "19.0.1.0.0",
    "license": "LGPL-3",
    "category": "Warehouse",
    "summary": "Return merchandise authorization module helps you to manage with product returns and exchanges.",
    "description": """"Return merchandise authorization module helps you to manage with product returns and exchanges.""",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "depends": [
        "sale_management",
        "sale",
        "sale_stock",
        "purchase_stock"
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/rma_data.xml",
        "views/res_company.xml",
        "views/rma_view.xml",
        "views/rms_reasons_view.xml",
        "views/rma_purchase_lines_view.xml",
        "views/rma_sale_lines_view.xml",
        "views/sale_views.xml",
        "views/purchase_views.xml",
        "views/stock_views.xml",
        "views/rma_direct_lines_view.xml",
        "views/rma_picking_lines_view.xml",
        "views/rma_sale_direct_lines_view.xml",
        "wizard/sale_return_import_wiz.xml",
        "wizard/create_so_line_wiz.xml",
        "report/report_mer_auth_rma.xml",
        "report/rma_report_mer_auth_reg.xml",
        "data/reason_data.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
    "pre_init_hook": "pre_init_hook",
}