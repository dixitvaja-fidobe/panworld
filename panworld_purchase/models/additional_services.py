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


class AdditionalServices(models.AbstractModel):
    _name = "additional.services"
    _description = "Additional Services"

    product_id = fields.Many2one(
        "product.product",
        string="Service",
        index=True,
        ondelete="restrict",
        domain=[("type", "=", "service"), ("landed_cost_ok", "=", True)],
        required=True,
    )
    product_qty = fields.Float(
        string="Quantity", digits="Product Unit of Measure", required=True, default=1.0
    )
    price_unit = fields.Float(
        string="Unit Price", required=True, digits="Product Price"
    )

    @api.onchange("product_id")
    def _onchange_product(self):
        self.ensure_one()
        if self.product_id:
            seller = self.product_id.with_company(self.env.company)._select_seller(
                partner_id=False,
                quantity=self.product_qty,
                date=fields.Date.today(),
                uom_id=self.product_id.uom_id,
            )
            price_unit = (
                self.env["account.tax"]._fix_tax_included_price_company(
                    seller.price,
                    self.product_id.supplier_taxes_id,
                    self.product_id.supplier_taxes_id,
                    self.env.company,
                )
                if seller
                else 0.0
            )
            self.price_unit = price_unit
        else:
            self.price_unit = 0.0
