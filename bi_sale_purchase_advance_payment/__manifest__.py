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
    'name': 'Advance Down Payment for Sales and Purchase',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Sale Advance payment and purchase advance payment',
    'description': """
        Sale Order and Purchase Order Advance Payment in odoo,
        Sale Order Advance Payment in odoo,
        Purchase Order Advance Payment in odoo,
        Make an Advance Payment from Sale and Purchase Order in odoo,
        Advance Payment in odoo,
        Advance Payments will be Listed in Payment Advance Tab in odoo.
        Advance Payment Wizard in odoo,
        Outstanding Credit balance in odoo,
        Outstanding Debit balance in odoo,
    """,
    "author": "Jumana | Fidobe Solutions",
    "maintainer": "Fidobe Solutions LLC.",
    "website": "www.fidobe.com",
    "license": "LGPL-3",
    'depends': ['sale_management',
                'purchase',
                'account',
                'stock',
                'mail',
                "account_batch_payment"],
    'data': [
        'security/ir.model.access.csv',
        'security/user_groups.xml',
        'wizard/sale_advance_payment_views.xml',
        'wizard/purchase_advance_payment_views.xml',
        'data/mail_template_request_adv_payment.xml',
        # 'views/sale_views.xml',
        'views/purchase_views.xml',
        'views/pending_advance_requests_view.xml',
        'views/account_payment.xml',

    ],
    "installable": True,
    "auto_install": False,
    "application": False
}
