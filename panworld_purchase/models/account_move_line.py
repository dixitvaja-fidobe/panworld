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
from odoo.tools import float_compare
from odoo.exceptions import ValidationError, UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    rma_sale_direct_line_id = fields.Many2one(
        'rma.sale.direct.lines', string='RMA Sale Direct Line', help='Compute marketplace cost base on rma sale direct line')
    rma_sale_line_id = fields.Many2one(
        'rma.sale.lines', string='RMA Sale Line', help='Compute marketplace cost base on rma sale line')
    customer_sales_order = fields.Char(string='Customer Sales Order')
    customer_name = fields.Char(string='Customer Name')
    is_allow_to_edit_bill_lines = fields.Boolean(compute='_compute_is_allow_to_edit_bill_lines')

    def _compute_is_allow_to_edit_bill_lines(self):
        if self.env.user.has_group('panworld_purchase.is_allow_to_edit_bill_lines_group'):
            self.is_allow_to_edit_bill_lines = True
        else:
            self.is_allow_to_edit_bill_lines = False