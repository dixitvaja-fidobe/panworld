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
    "name": "Panworld Account",
    "version": "19.0.1.0.0",
    "category": "account",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "panworld_purchase",
        "panworld_sale",
        "account",
        "l10n_ae",
        "account_asset",
        "costing_reports",
        "report_xlsx",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/account_move_views.xml",
        "views/res_partner_views.xml",
        "views/shipping_service_views.xml",
        # "views/res_config_settings_views.xml",
        "views/account_journal.xml",
        "views/account_move_line_views.xml",
        "wizards/update_wiz_views.xml",
        "views/account_asset_views.xml",
        "report/panworld_invoice_excel_report.xml",
        "views/account_payment_views.xml",
        "views/account_account_views.xml"
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
