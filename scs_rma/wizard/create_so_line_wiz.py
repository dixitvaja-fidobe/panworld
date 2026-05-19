# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################

from odoo import models, fields
import datetime
import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class CreateSOLineWizard(models.TransientModel):
    _name = "create.so.line.wiz"

    rma_id = fields.Many2one('rma.ret.mer.auth',string="RMA")
    sale_id = fields.Many2one('sale.order',string="Sale")
    wiz_line_ids = fields.One2many('create.so.line','wiz_id')

    def action_create_so_line(self):
        """Create SO lines in the linked Sale Order using wizard lines."""
        self.ensure_one()

        if not self.sale_id:
            raise UserError("No Sale Order linked to this wizard.")

        for line in self.wiz_line_ids:
            self.env['sale.order.line'].create({
                'order_id': self.sale_id.id,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty,
                'price_unit': line.price_unit,
            })

        if self.rma_id:
            self.rma_id.so_lines_created = True

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'rma.ret.mer.auth',
            'view_mode': 'form',
            'res_id': self.rma_id.id,
        }


class CreateSOLine(models.TransientModel):
    _name = "create.so.line"

    wiz_id = fields.Many2one('create.so.line.wiz')
    product_id = fields.Many2one('product.product',string="Product")
    product_qty = fields.Float(string="SO Qty")
    price_unit = fields.Float(string="Unit Price", digits="Product Price")