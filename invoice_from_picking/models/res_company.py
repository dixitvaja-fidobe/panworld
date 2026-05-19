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

class ResCompany(models.Model):
    """Add extra fields to the configuration settings page"""
    _inherit = 'res.company'

    pw_invoice_terms = fields.Html(string='Default Terms and Conditions', translate=True)
