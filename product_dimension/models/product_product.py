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


class ProductProduct(models.Model):
    _inherit = "product.product"

    product_length = fields.Float("length")
    product_height = fields.Float("height")
    product_width = fields.Float("width")
    dimensional_uom_id = fields.Many2one(
        "uom.uom",
        "Dimensional UoM",
        domain=lambda self: self._get_dimension_uom_domain(),
        help="UoM for length, height, width",
        default=lambda self: self._get_default_dimension_uom()
    )
    volume = fields.Float(
        compute="_compute_volume",
        readonly=False,
        store=True,
    )

    @api.depends(
        "product_length", "product_height", "product_width", "dimensional_uom_id"
    )
    def _compute_volume(self):
        template_obj = self.env["product.template"]
        for product in self:
            product.volume = template_obj._calc_volume(
                product.product_length,
                product.product_height,
                product.product_width,
                product.dimensional_uom_id,
            )

    @api.model
    def _get_dimension_uom_domain(self):
        """Get domain for dimension UoM - handle case when category doesn't exist"""
        try:
            # Try to get the length category, fallback to any category if not found
            length_category = self.env.ref('uom.uom_categ_length', False)
            if length_category:
                return [('category_id', '=', length_category.id)]
            else:
                # If length category doesn't exist, don't restrict domain
                return []
        except:
            return []

    @api.model
    def _get_default_dimension_uom(self):
        """Get default dimension UoM - handle case when meter doesn't exist"""
        try:
            return self.env.ref('uom.product_uom_meter', False) or False
        except:
            return False
