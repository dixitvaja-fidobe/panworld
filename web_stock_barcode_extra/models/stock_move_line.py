# -*- coding: utf-8 -*-

from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    customer_sales_order = fields.Char(related='move_id.customer_sales_order', readonly=True)
    customer_name = fields.Char(related='move_id.customer_name', readonly=True)
    product_uom_qty = fields.Float(related='move_id.product_uom_qty', readonly=True)

    def _get_fields_stock_barcode(self):
        res = super(StockMoveLine, self)._get_fields_stock_barcode()
        res.append('customer_sales_order')
        res.append('customer_name')
        res.append('product_uom_qty')
        return res
