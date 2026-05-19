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


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    csn_no = fields.Char("C.S.N")
    word_count = fields.Integer(string="Word Count", compute='_compute_values')
    cost_per_unit = fields.Float(string="Cost/Unit", digits=(16, 3), compute='_compute_values')

    @api.depends('sale_line_ids.word_count', 'sale_line_ids.cost_per_unit')
    def _compute_values(self):
        for line in self:
            line.word_count = sum(line.sale_line_ids.mapped('word_count'))
            line.cost_per_unit = sum(line.sale_line_ids.mapped('cost_per_unit'))
            # Commented as on 06-10-25 since the word count and cost is reported as changing after invoice posting.
            # if line.word_count>0 and line.cost_per_unit>0:
            #     line.price_unit = round(line.word_count * line.cost_per_unit, 2)
