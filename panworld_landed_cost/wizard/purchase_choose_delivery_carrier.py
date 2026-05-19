# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from multiprocessing import context
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class PurchaseChooseDeliveryCarrier(models.TransientModel):
    _name = "purchase.choose.delivery.carrier"
    _description = "Purchase Delivery Carrier Selection Wizard"

    stock_landed_cost_id = fields.Many2one("stock.landed.cost")
    purchase_order_id = fields.Many2one("purchase.order")
    purchase_partner_id = fields.Many2one(
        "res.partner", related="purchase_order_id.partner_id", required=True
    )
    purchase_currency_id = fields.Many2one(
        "res.currency", related="purchase_order_id.company_currency_id"
    )
    purchase_company_id = fields.Many2one(
        "res.company", related="purchase_order_id.company_id"
    )
    carrier_id = fields.Many2one(
        "delivery.carrier",
        string="Shipping Method",
        help="Choose the method to deliver your goods",
        domain="[('carrier_type','=','purchase')]",
        required=True,
    )
    delivery_type = fields.Selection(related="carrier_id.delivery_type")
    delivery_price = fields.Float()
    display_price = fields.Float(string="Cost", readonly=True)
    available_carrier_ids = fields.Many2many(
        "delivery.carrier",
        compute="_compute_available_carrier",
        string="Available Carriers",
    )
    invoicing_message = fields.Text(compute="_compute_invoicing_message")
    delivery_message = fields.Text(readonly=True)
    delivery_weight = fields.Float("Weight")
    consolidated_weight = fields.Float("Consolidated Weight")

    @api.depends("purchase_partner_id")
    def _compute_available_carrier(self):
        for record in self:
            carriers = self.env["delivery.carrier"].search([
                "|",
                ("company_id", "=", False),
                ("company_id", "=", record.purchase_order_id.company_id.id),
            ])
            record.available_carrier_ids = (
                carriers.available_carriers(
                    record.purchase_order_id.partner_id,
                    record.purchase_order_id,
                )
                if record.purchase_partner_id
                else carriers
            )

    @api.depends("carrier_id")
    def _compute_invoicing_message(self):
        self.ensure_one()
        if self.carrier_id.invoice_policy == "real":
            self.invoicing_message = _(
                "The shipping price will be set once the delivery is done."
            )
        else:
            self.invoicing_message = ""

    @api.onchange("consolidated_weight", "carrier_id")
    def _onchange_delivery_weight(self):
        price = self.carrier_id._get_price_from_picking(
            0.0, self.consolidated_weight, 0.0, 1.0
        )
        self.delivery_price = price
        self.display_price = price

    @api.constrains("consolidated_weight", "delivery_weight")
    def _check_consolidated_weight(self):
        for rec in self:
            if rec.consolidated_weight < rec.delivery_weight:
                raise ValidationError(
                    "Consolidated weight must be equal or greater than weight!")

    @api.onchange("purchase_order_id")
    def _onchange_order_id(self):
        if self.carrier_id and self.purchase_order_id.delivery_set and self.delivery_type not in ("fixed", "base_on_rule"):
            vals = self._purchase_get_shipment_rate()
            if vals.get("error_message"):
                warning = {
                    "title": "%s Error" % self.carrier_id.name,
                    "message": vals.get("error_message"),
                    "type": "notification",
                }
                return {"warning": warning}
        return None

    def _get_delivery_weight(self, order):
        weight = 0.0
        total_delivery = 0
        for line in order.order_line:
            if line.state == "cancel":
                continue
            if line.is_delivery:
                total_delivery += line.price_total
            if not line.product_id or line.is_delivery:
                continue
            if line.product_id.type == "service":
                continue
            qty = line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id)
            weight += (line.product_id.weight or 0.0) * qty
        return weight

    def _purchase_get_shipment_rate(self):
        order = ""
        msg = "Please Configure Transfer in Landed cost !"
        if self.purchase_order_id:
            order = self.purchase_order_id
            msg = "Please Configure purchase order !"
        purchase_orders = (
            self.stock_landed_cost_id
            and self.stock_landed_cost_id.picking_ids.mapped("purchase_ids")
        )
        if purchase_orders:
            order = purchase_orders[0]
        if not order:
            raise UserError(_(msg))
        vals = self.carrier_id.rate_shipment(order)
        if vals.get("success"):
            self.delivery_message = vals.get("warning_message", False)
            self.delivery_price = vals.get("price", False)
            self.display_price = vals.get("carrier_price", False)
            if self.purchase_order_id:
                self.delivery_weight = self._get_delivery_weight(self.purchase_order_id)
            if self.stock_landed_cost_id and self.env.context.get(
                "default_delivery_weight"
            ):
                self.delivery_weight = self.env.context.get("default_delivery_weight")
            if self.consolidated_weight > 0:
                self.display_price = vals.get("carrier_price")
            return {}
        return {"error_message": vals["error_message"]}

    def update_price(self):
        vals = self._purchase_get_shipment_rate()
        if vals.get("error_message"):
            raise UserError(vals.get("error_message"))
        return {
            "name": _("Add a shipping method"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "choose.delivery.carrier",
            "res_id": self.id,
            "target": "new",
        }

    def button_confirm(self):
        # Purchase Module
        if self.env.context.get("active_model") == "purchase.order":
            purchase_rec = self.env["purchase.order"].browse(self.env.context.get("active_ids"))
            if purchase_rec:
                purchase_rec.write({"consolidated_weight": self.consolidated_weight})

        if self.purchase_order_id:
            self.purchase_order_id.set_purchase_delivery_line(
                self.carrier_id,
                self.delivery_price,
                self.delivery_weight,
                self.consolidated_weight,
            )

        # Stock Module
        if self.env.context.get("active_model") == "stock.landed.cost" and self.env.context.get("active_ids"):
            landed_cost_rec = self.env["stock.landed.cost"].browse(self.env.context.get("active_ids"))
            if landed_cost_rec:
                landed_cost_rec.write({"consolidated_weight": self.consolidated_weight,
                                       "shipping_cost_bool": True})
        if self.stock_landed_cost_id:
            self.stock_landed_cost_id.set_landed_cost_delivery_line(
                self.carrier_id,
                self.delivery_price,
                self.delivery_weight,
                self.consolidated_weight,
            )
