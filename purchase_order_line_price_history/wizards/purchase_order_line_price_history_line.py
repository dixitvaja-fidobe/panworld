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


class PurchaseOrderLinePriceHistoryLine(models.TransientModel):
    _name = "purchase.order.line.price.history.line"
    _description = "Purchase order line price history line"

    history_id = fields.Many2one(
        comodel_name="purchase.order.line.price.history", string="History",
    )
    purchase_order_line_id = fields.Many2one(
        comodel_name="purchase.order.line", string="Purchase order line",
    )
    order_id = fields.Many2one(related="purchase_order_line_id.order_id")
    partner_id = fields.Many2one(related="purchase_order_line_id.partner_id")
    purchase_order_date_order = fields.Datetime(
        related="purchase_order_line_id.order_id.date_order",
    )
    product_qty = fields.Float(related="purchase_order_line_id.product_qty")
    product_uom = fields.Many2one(related="purchase_order_line_id.product_uom_id")
    price_unit = fields.Float(related="purchase_order_line_id.price_unit")

    def _prepare_purchase_order_line_vals(self):
        self.ensure_one()
        return {"price_unit": self.price_unit}

    def action_set_price(self):
        self.ensure_one()
        active_id = self.env.context.get("active_id")
        order_line = self.env["purchase.order.line"].browse(active_id)
        vals = self._prepare_purchase_order_line_vals()
        order_line.write(vals)