# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import fields,models, api

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_bundle_product = fields.Boolean(string="Is Bundle", compute="_compute_is_bundle_product", store=False)

    @api.depends('product_id.product_tmpl_id.bom_ids', 'product_id.product_tmpl_id.bom_ids.type')
    def _compute_is_bundle_product(self):
        tmpl_ids = self.mapped('product_id.product_tmpl_id').ids
        if not tmpl_ids:
            self.is_bundle_product = False
            return
        boms = self.env['mrp.bom'].search([
            ('product_tmpl_id', 'in', tmpl_ids),
            ('type', '=', 'phantom')
        ])
        bundle_tmpl_ids = set(boms.mapped('product_tmpl_id.id'))
        for line in self:
            line.is_bundle_product = line.product_id.product_tmpl_id.id in bundle_tmpl_ids
