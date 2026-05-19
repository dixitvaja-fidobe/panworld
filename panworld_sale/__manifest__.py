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
    "name": "Panworld Sale",
    "version": "19.0.1.0.0",
    "category": "sale",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": ["sale",
                "delivery",
                "panworld_contact",
                "panworld_products",
                "panworld_purchase",
                "so_compare_cancel_line",
                "po_compare_cancel_line",
                "scs_rma",
                "scs_sale_purchase",
                "sale_purchase_inter_company_rules",
                "sale_purchase_stock_inter_company_rules",
                "spreadsheet_dashboard_sale"
                ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/sale_quote_date.xml",
        "views/sale_order_views.xml",
        "views/res_partner_views.xml",
        "views/res_partner_view.xml",
        "views/sale_price_history_views.xml",
        "views/stock_picking_views.xml",
        "views/academic_year_views.xml",
        "views/account_move_views.xml",
        "views/sale_report_views.xml",
        "data/spreadsheet_dashboard_data.xml",
        "wizard/wiz_update_order_date.xml"
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
