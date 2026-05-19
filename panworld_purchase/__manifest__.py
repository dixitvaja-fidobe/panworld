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
    "name": "Panworld Purchase",
    "version": "19.0.1.0.0",
    "category": "Purchase",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "stock_delivery",
        "stock_picking_batch",
        # custom addons
        "po_compare_cancel_line",
        "scs_sale_purchase",
        "purchase_discount",
        "purchase_tier_validation",
        "base_tier_validation_forward",
        "purchase_order_type",
        "purchase_request",
        "purchase_order_line_price_history",
        "panworld_bill_variance",
        "costing_reports",
        "stock_dropshipping"
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        'security/user_groups.xml',
        "data/purchase_order_tier_definition.xml",
        "data/purchase_order_tier_definition.xml",
        "data/purchase_request_sequence.xml",
        # "data/mail_template_grn_data.xml",
        # "data/purchase_tracker_mail_cron.xml",
        # "report/panworld_purchase_order_templates.xml",
        # "report/panworld_purchase_quotation_templates.xml",
        "wizard/check_price_change_views.xml",
        "views/account_views.xml",
        "views/purchase_order_views.xml",
        "views/purchase_order_type_views.xml",
        # "views/purchase_request_line_view.xml",
        "views/purchase_shipping_options.xml",
        # "views/stock_picking_batch.xml",
        "views/stock_picking_view.xml",
        "views/purchase_tracker_view.xml",
        # "views/res_company_views.xml",
        "wizard/purchase_order_status_report.xml",
        "wizard/purchase_order_tracker_wizard.xml",
        "wizard/wizard.xml",
        "wizard/cancel_reason_wizard_view.xml",
        "views/purchase_request_view.xml",
        "views/purchase_price_history_views.xml",
        "views/service_quotation_views.xml",
        "views/delivery_carrier_view.xml"

    ],
    'assets': {
        'web.report_assets_common': [
            'panworld_purchase/static/src/scss/layout_standard.scss',
        ],
        'web.assets_backend': [
            'panworld_purchase/static/src/components/tax_totals/tax_totals.xml',
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": False
}
