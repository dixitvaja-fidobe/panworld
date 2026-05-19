# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_validation_exempt = fields.Boolean(string="Exempt From Validation")
    purchase_account_number = fields.Char(
        string="Purchase Account Number",
        company_dependent=True,
        help="Purchase Account Number")