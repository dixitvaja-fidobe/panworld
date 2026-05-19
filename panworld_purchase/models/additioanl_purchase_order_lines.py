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

class AdditionalPurchaseOrderLines(models.Model):
    _name = "additional.purchase.order.lines"
    _description = "Additional Purchase Order Lines"
    _inherit = [
        "additional.services",
    ]

    @api.depends("product_qty", "price_unit", "taxes_id")
    def _compute_amount(self):
        for line in self:
            taxes = line.taxes_id.compute_all(**line._prepare_compute_all_values())
            line.update(
                {
                    "price_tax": taxes["total_included"] - taxes["total_excluded"],
                    "price_total": taxes["total_included"],
                    "price_subtotal": taxes["total_excluded"],
                }
            )

    def _prepare_compute_all_values(self):
        self.ensure_one()
        return {
            "price_unit": self.price_unit,
            "currency": self.order_id.currency_id,
            "quantity": self.product_qty,
            "product": self.product_id,
            "partner": self.order_id.partner_id,
        }

    name = fields.Text("Description")
    order_id = fields.Many2one(
        "purchase.order", string="Purchase Order", copy=False, ondelete="cascade"
    )
    consolidated_price = fields.Float(
        string="Consolidated Price", required=True, digits="Product Price"
    )
    taxes_id = fields.Many2many(
        "account.tax",
        string="Taxes",
        domain=["|", ("active", "=", False), ("active", "=", True)],
    )
    # product_uom_category_id = fields.Many2one(related="product_id.uom_id.category_id")
    product_uom = fields.Many2one(
        "uom.uom",
        string="Unit of Measure",
        # domain="[('category_id', '=', product_uom_category_id)]",
    )
    currency_id = fields.Many2one(
        related="order_id.currency_id", store=True, string="Currency", readonly=True
    )
    price_subtotal = fields.Monetary(
        compute="_compute_amount", string="Subtotal", store=True
    )
    price_total = fields.Monetary(compute="_compute_amount", string="Total", store=True)
    price_tax = fields.Float(compute="_compute_amount", string="Tax", store=True)
