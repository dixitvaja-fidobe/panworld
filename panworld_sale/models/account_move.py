# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import _, api, fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    academic_year_id = fields.Many2one("academic.year", string="Academic Year",
                                       compute='_compute_academic_year_id', store=True)

    @api.depends('invoice_line_ids.sale_line_ids.order_id.academic_year_id')
    def _compute_academic_year_id(self):
        """Add value for academic year from respective sale orders"""
        for move in self:
            academic_year = None
            sale_orders = move.invoice_line_ids.mapped('sale_line_ids.order_id')
            if sale_orders:
                academic_year = sale_orders.filtered(lambda so: so.academic_year_id)[:1].academic_year_id
            move.academic_year_id = academic_year

