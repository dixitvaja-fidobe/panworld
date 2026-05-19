# -*- coding: utf-8 -*-
from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    bank_details = fields.Html(
        related='company_id.bank_details',
        string="Bank Details",
        readonly=False,
        translate=True
    )
    bank_details_ar = fields.Html(
        related='company_id.bank_details_ar',
        string="Bank Details Arabic",
        readonly=False,
        translate=True
    )
    payment_term_condition_ar = fields.Html(
        related='company_id.payment_term_condition_ar',
        string="Payment Term Condition Arabic",
        readonly=False,
        translate=True
    )
