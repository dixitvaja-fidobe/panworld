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


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    csn_no = fields.Char("C.S.N")
    word_count = fields.Integer("Word Count", )
    cost_per_unit = fields.Float("Cost/Unit", digits=(16, 3))

    @api.onchange('word_count', 'cost_per_unit')
    def _onchange_word_count_cost(self):
        for line in self:
            if line.word_count and line.cost_per_unit:
                line.product_uom_qty = line.word_count
                line.price_unit = line.cost_per_unit

    def _prepare_invoice_line(self, **optional_values):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        :param optional_values: any parameter that should be added to the returned invoice line
        """
        values = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        if not values.get('csn_no'):
            values['csn_no'] = self.csn_no
        return values
