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
    "name": "Panworld Email Configuration",
    "version": "19.0.1.0.0",
    "category": "Purchase",
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    "depends": ["panworld_sale",
                "panworld_purchase",
                "purchase",
                "sale",
                "mail",
                "account_reports"],
    "data": [
        "security/ir.model.access.csv",
        # "data/mail_template_data_sale.xml",
        # "data/mail_template_data_sale_confirm.xml",
        # "data/mail_template_data_purchase.xml",
        # "data/mail_template_data_purchase_po.xml",
        # "data/mail_template_data_purchase_po_remider.xml",
        # "data/mail_template_data_invoice.xml",
        # "views/mail_notification_wizard_inherit.xml",
        "wizard/partner_ladger_wizard_view.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
