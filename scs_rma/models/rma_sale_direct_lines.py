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
from odoo.exceptions import ValidationError


class RmaSaleDirectLines(models.Model):
    _name = "rma.sale.direct.lines"
    _description = "Return Merchandise Authorization Sale Direct Lines"

    @api.model
    def _get_source_location(self):
        return self.env.user.company_id.source_location_id or self.env["stock.location"]

    @api.model
    def _get_destination_location(self):
        return (
            self.env.user.company_id.destination_location_id
            or self.env["stock.location"]
        )

    rma_id = fields.Many2one("rma.ret.mer.auth", "RMA")
    product_id = fields.Many2one("product.product", "Product")
    reason_id = fields.Many2one("rma.reasons", string="Reason")
    reason = fields.Text(string="Reason")
    currency_id = fields.Many2one(
        "res.currency",
        related="rma_id.company_id.currency_id",
        string="Currency",
        readonly=True,
    )
    total_qty = fields.Integer(string="Total Qty", readonly=False)
    order_quantity = fields.Integer("Ordered Qty")
    delivered_quantity = fields.Integer("Delivered Qty")
    price_unit = fields.Float("Unit Price", digits="Product Price")
    refund_qty = fields.Integer("Return Qty")
    refund_price = fields.Float(
        compute="_compute_amount", string="Refund Price", compute_sudo=True, store=True, digits="Product Price"
    )
    total_price = fields.Float(string="Total Price")
    type = fields.Selection([("return", "Return")], string="Action", default="return", )
    tax_id = fields.Many2many(
        "account.tax",
        "account_tax_rma_sale_direct_lines_rel",
        "rma_sale_direct_lines_id",
        "account_tax_id",
        string="Taxes"
    )
    price_subtotal = fields.Float(
        compute="_compute_amount",
        string="Subtotal",
        readonly=True,
        store=True,
        compute_sudo=True,
    )
    price_tax = fields.Float(
        compute="_compute_amount",
        string="Taxes",
        readonly=True,
        store=True,
        compute_sudo=True,
    )
    price_total = fields.Float(
        compute="_compute_amount",
        string="Total",
        readonly=True,
        store=True,
        compute_sudo=True,
    )
    source_location_id = fields.Many2one(
        "stock.location", "Source Location", default=_get_source_location
    )
    destination_location_id = fields.Many2one(
        "stock.location", "Destination Location", default=_get_destination_location
    )
    landed_cost = fields.Float("LCO")
    marketplace_cost = fields.Float(string="MCO")
    shipping_cost = fields.Float(string="SCO")
    other_cost = fields.Float(string="OCO")
    subtotal_cost = fields.Float(string="TCO")

    @api.depends("refund_qty", "price_unit", "tax_id")
    def _compute_amount(self):
        """Compute the amounts of the SO line."""
        for line in self:
            refund_qty = line.refund_qty
            price = line.price_unit
            taxes = line.tax_id.compute_all(
                price,
                line.rma_id.currency_id,
                refund_qty,
                product=line.product_id,
                partner=line.rma_id.partner_id,
            )
            line.price_tax = taxes["total_included"] - taxes["total_excluded"]
            line.refund_price = refund_qty * price
            line.price_subtotal = taxes["total_excluded"]
            line.price_total = taxes["total_included"]

    @api.model_create_multi
    def create(self, vals_list):
        res = super(RmaSaleDirectLines, self).create(vals_list)
        for record in res:
            if not record.source_location_id or not record.destination_location_id:
                raise ValidationError(
                    _(
                        "Please Configure valid source and destination location in your company!"
                    )
                )
        return res

    @api.constrains("total_qty", "refund_qty")
    def _check_rma_quantity(self):
        for line in self:
            if line.total_qty != 0.0 and line.refund_qty > line.total_qty:
                raise ValidationError(
                    "Return Quantity should not be greater \
                  than Total Quantity."
                )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res.update(
            {
                "source_location_id": self.env.company.source_location_id.id,
                "destination_location_id": self.env.company.destination_location_id.id,
            }
        )
        return res

    @api.onchange("refund_qty", "total_qty")
    def _onchange_refund_price(self):
        for order in self:
            if order.total_qty != 0.0 and order.refund_qty > order.total_qty:
                raise ValidationError(
                    "Return Quantity should not be greater than Total Quantity."
                )
            total_qty_amt = 0.0
            if order.total_price and order.total_qty:
                total_qty_amt = (order.total_price / order.total_qty) * float(
                    order.refund_qty
                )
                order.refund_price = total_qty_amt
            else:
                if order.product_id and order.product_id.id:
                    order.refund_price = order.product_id.lst_price * order.refund_qty
