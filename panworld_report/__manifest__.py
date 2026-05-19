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
    "name": "Panworld Report",
    "version": "19.0.1.0.0",
    "summary": "Panworld Report Customizations",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": [
        "account",
        "stock",
        "sale",
        "panworld_sale",
        "panworld_purchase",
        "l10n_ae",
        "l10n_sa",
        "sale_pdf_quote_builder",
        "panworld_saudi_arabic_invoice"
    ],
    "data": [
            "security/ir.model.access.csv",
            "report/panworld_sale_order_templates.xml",
            # "report/panworld_sale_order_landscape.xml",
            "report/report_purchase_quotation_document.xml",
            "report/report_purchase_order_document.xml",
            "report/report_invoice_document.xml",
            "report/report_delivery_document.xml",
            "report/report_delivery_slip_bundle.xml",
            "report/report_delivery_slip_for_export.xml",
            "report/report_credit_note_custom.xml",
            "report/report_invoice_export_sales.xml",
            "report/panworld_invoice_report_uaeu.xml",
            "report/report_actions.xml",
            "wizard/export_sale_xls_view.xml",
            "wizard/import_transfer_wizard_view.xml",
            "wizard/choose_delivery_carrier_views.xml",
            "wizard/sale_order_status_report.xml",
            "wizard/sale_order_xls.xml",
            "wizard/purchase_register_report_wizard_view.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
