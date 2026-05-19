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


class WizSalePurchaseLine(models.TransientModel):
    """Wiz Sale Purchase Line model."""

    _name = "wiz.sale.purchase.line"
    _description = "Wizard Sale Purchase Line"

    product_id = fields.Many2one("product.product", string="Product")
    wiz_sale_purchase_id = fields.Many2one(
        "wiz.sale.purchase", string="Wiz Sale Purchase"
    )
    sale_line_id  = fields.Many2one('sale.order.line', string="sale Order Line")
    name = fields.Text(string="Description")
    qty = fields.Float(string="Quantity")
    price_unit = fields.Float(string="Unit Price")
    subtotal = fields.Float(compute="_compute_sub_total", store=True, string="Subtotal")
    uom_id = fields.Many2one("uom.uom", "UoM")
    vendor_id = fields.Many2one("res.partner", string="Vendor")
    taxes_id = fields.Many2many("account.tax", string="Taxes",)
    l10n_in_gst_treatment = fields.Selection(
        [
            ("regular", "Registered Business - Regular"),
            ("composition", "Registered Business - Composition"),
            ("unregistered", "Unregistered Business"),
            ("consumer", "Consumer"),
            ("overseas", "Overseas"),
            ("special_economic_zone", "Special Economic Zone"),
            ("deemed_export", "Deemed Export"),
        ],
        string="GST Treatment",
    )
    l10n_in_company_country_code = fields.Char(
        related="wiz_sale_purchase_id.l10n_in_company_country_code",
        string="Country code",
        store=True,
    )
    l10n_in_purchase = fields.Boolean(
        related="wiz_sale_purchase_id.l10n_in_purchase",
        string="Is l10n In Purchase?",
        store=True,
    )
    l10n_in_sale = fields.Boolean(
        related="wiz_sale_purchase_id.l10n_in_sale",
        string="Is l10n In Sale?",
        store=True,
    )
    sale_reference = fields.Char('Sale Origin')

    @api.onchange("product_id")
    def _onchange_product_id(self):
        """Onchange to calculate the subtotal."""
        product_des = ""
        product = self.product_id
        vendor_price = 1.0
        if product:
            code = product.default_code and "[" + product.default_code + "] " or ""
            product_des = code + product.name or ""

        if self.wiz_sale_purchase_id.vendor_option == "single":
            if self.wiz_sale_purchase_id.vendor_id:
                vendor_price = self.product_id.seller_ids.filtered(
                    lambda v: v.partner_id.name == self.wiz_sale_purchase_id.vendor_id
                ).mapped("price")
                vendor_price = (
                    min(vendor_price)
                    if vendor_price
                    else self.product_id.standard_price or 1.0
                )
        else:
            if self.product_id.seller_ids:
                self.vendor_id = self.product_id.seller_ids[0].partner_id.name or False
                self.price_unit = self.product_id.seller_ids[0].price or False

        self.update(
            {
                "name": product_des or "",
                "price_unit": vendor_price,
                "qty": self.qty or 1.0,
                "uom_id": product
                and product.uom_po_id
                or product
                and product.uom_id
                or False,
                "taxes_id": product
                and [
                    (
                        6,
                        0,
                        product.supplier_taxes_id
                        and product.supplier_taxes_id.ids
                        or [],
                    )
                ]
                or [],
            }
        )

    @api.onchange("vendor_id", "wiz_sale_purchase_id")
    def onchange_vendor_id(self):
        for line in self:
            if line.wiz_sale_purchase_id.vendor_option == "multi":
                if line.vendor_id:
                    vendor_price = line.product_id.seller_ids.filtered(
                        lambda v: v.partner_id.name == line.vendor_id
                    ).mapped("price")
                    line.price_unit = (
                        min(vendor_price)
                        if vendor_price
                        else line.product_id.standard_price or 1.0
                    )
            if line.wiz_sale_purchase_id.vendor_option == "single":
                line.vendor_id = False

    @api.depends("qty", "price_unit")
    def _compute_sub_total(self):
        """Method to compute the subtotal."""
        for line in self:
            line.subtotal = line.qty * line.price_unit
