# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from itertools import groupby
from odoo import _, api, Command, fields, models
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class StockMove(models.Model):
    _inherit = "stock.move"

    def _assign_picking(self):
        if self.env.context.get('is_backorder'):
            """Override Function for create new move/picking"""
            Picking = self.env['stock.picking']
            grouped_moves = groupby(sorted(self, key=lambda m: [f.id for f in m._key_assign_picking()]),
                                    key=lambda m: [m._key_assign_picking()])
            for group, moves in grouped_moves:
                moves = self.env['stock.move'].concat(*list(moves))
                moves = moves.filtered(
                    lambda m: float_compare(m.product_uom_qty, 0.0, precision_rounding=m.product_uom.rounding) >= 0)
                if not moves:
                    continue
                new_picking = True
                picking_vals = moves._get_new_picking_values()
                
                # Ensure sale_id and purchase_id are propagated to the new picking
                # These are often lost when manually creating pickings outside standard sale_stock/purchase_stock flows
                sale_id = moves.mapped('sale_line_id.order_id')[:1].id
                purchase_id = moves.mapped('purchase_line_id.order_id')[:1].id
                
                if sale_id:
                    picking_vals['sale_id'] = sale_id
                if purchase_id:
                    picking_vals['purchase_id'] = purchase_id
                
                # Also copy custom fields from the first move's current picking if they exist
                parent_picking = moves[:1].picking_id
                if parent_picking:
                    for field in ['analytic_account_id', 'division_type_id', 'carrier_id']:
                        if field in parent_picking._fields and not picking_vals.get(field):
                            picking_vals[field] = parent_picking[field].id if hasattr(parent_picking[field], 'id') else parent_picking[field]

                picking = Picking.create(picking_vals)
                moves.write({'picking_id': picking.id})
                moves._assign_picking_post_process(new=new_picking)
            return True
        else:
            return super()._assign_picking()

    def _prepare_procurement_values(self):
        """Ensure partner_id is propagated to chained moves, resolving missing partner on internal pickings."""
        values = super()._prepare_procurement_values()
        if self.partner_id:
            values['partner_id'] = self.partner_id.id
        return values