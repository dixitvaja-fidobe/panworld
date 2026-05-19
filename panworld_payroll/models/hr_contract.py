# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = "hr.contract"

    analytic_tag_id = fields.Many2one('account.analytic.tag', string='Analytic Tag')
