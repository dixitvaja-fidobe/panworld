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


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    shipping_weight = fields.Float(
        string='Shipping Weight',
        compute='_compute_shipping_weight',
        store=True
    )

    @api.depends('order_line.product_qty', 'order_line.product_id', 'order_line.product_uom_id')
    def _compute_shipping_weight(self):
        for order in self:
            weight = 0.0
            for line in order.order_line:
                if line.state == 'cancel' or line.product_id.type == 'service':
                    continue
                qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_id)
                weight += (line.product_id.weight or 0.0) * qty
            order.shipping_weight = weight

    def action_open_delivery_wizard(self):
        view_id = self.env.ref("panworld_landed_cost.purchase_choose_delivery_carrier_view_form").id
        if self.env.context.get("carrier_recompute"):
            name = _("Update shipping cost")
        else:
            name = _("Add a shipping method")
        ctx = {
            "default_purchase_order_id": self.id,
            "default_carrier_id": self.carrier_id and self.carrier_id.id or False,
            "default_delivery_weight": self.total_weight,
            "default_consolidated_weight": self.consolidated_weight and self.consolidated_weight or self.total_weight,
        }
        if self.consolidated_weight > 0:
            vals = self.carrier_id.rate_shipment(self)
            display_price = (
                                    vals["carrier_price"] * self.total_weight
                            ) / self.consolidated_weight
            ctx.update({"default_display_price": display_price})
        return {
            "name": name,
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "purchase.choose.delivery.carrier",
            "view_id": view_id,
            "views": [(view_id, "form")],
            "target": "new",
            "context": ctx,
        }


