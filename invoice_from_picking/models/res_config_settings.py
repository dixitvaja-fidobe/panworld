# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import api, fields, models, _

class ResConfigSettings(models.TransientModel):
    """Add extra fields to the configuration settings page"""
    _inherit = 'res.config.settings'

    pw_invoice_terms = fields.Html(related='company_id.pw_invoice_terms', string="Terms & Conditions", readonly=False)
    use_pw_invoice_terms = fields.Boolean(
        string='Default Terms & Conditions for Invoices only',
        config_parameter='invoice_from_picking.use_pw_invoice_terms')
