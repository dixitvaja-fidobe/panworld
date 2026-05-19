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

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    product_bundle_lines_count = fields.Integer("No. of Bundles", compute="_compute_bundle_count", store=True)
    bundle_total_qty = fields.Integer("Bundle Qty", compute="_compute_bundle_count", store=True)

    @api.depends('order_line.product_id', 'order_line.product_uom_qty')
    def _compute_bundle_count(self):
        """Get total bundle product quantity."""
        for order in self:
            # Batch optimization: Identify which lines are bundles
            tmpl_ids = order.order_line.mapped('product_id.product_tmpl_id').ids
            if not tmpl_ids:
                order.product_bundle_lines_count = 0
                order.bundle_total_qty = 0
                continue

            boms = self.env['mrp.bom'].search([
                ('product_tmpl_id', 'in', tmpl_ids),
                ('type', '=', 'phantom')
            ])
            bundle_tmpl_ids = set(boms.mapped('product_tmpl_id.id'))
            
            # Filter lines that match a bundle template
            bundle_lines = order.order_line.filtered(lambda l: l.product_id.product_tmpl_id.id in bundle_tmpl_ids)
            
            order.product_bundle_lines_count = len(bundle_lines)
            order.bundle_total_qty = sum(line.product_uom_qty for line in bundle_lines)
