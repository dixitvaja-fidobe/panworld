# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
import logging
_logger = logging.getLogger(__name__)
from odoo import api, fields, models, _
from odoo.tools import float_compare, float_round

class SoLCCl(models.Model):
    _inherit = 'sale.order.line'

    action = fields.Selection(string="Action",
                              selection=[('backorder', 'Backorder'), ('cancel', 'Cancel')],
                              required=False, copy=False)
    cancel_reason = fields.Selection(string="Cancel Reason", selection=[
        ('forthcoming', 'Forthcoming'), ('out_of_print', 'Out Of Print'),
        ('out_of_stock', 'Out Of Stock'), ('pod', 'Print On Demand'),
        ('new_edition', 'New Edition'), ('discontinued', 'Discontinued'),
        ('vendor_change', 'Vendor Change'), ('rights_restricted', 'Rights Restricted'),
        ('bundle_book', 'Bundle Book'), ('market_restricted', 'Market Restricted'),
        ('sale_restricted', 'Sale Restricted'), ('bo', 'Back Order'),
        ('reprinting', 'Reprinting'), ('min_qty_req', 'Minimum Qty/Amount Required'),
        ('vendor_not_found', 'Vendor Not Found'), ('without_budget', 'Without Budget'),
        ('nmc_rest', 'NMC Restriction'),('unavailable', 'Unavailable'),
        ('non_books', 'Non Books'),('oss', 'OOS Delivered'),('replaced', 'Replaced in another Order'),],
                                     copy=False)
    quote_cancel_reason = fields.Selection(string="Quote Cancel Reason", selection=[
        ('forthcoming', 'Forthcoming'), ('out_of_print', 'Out Of Print'),
        ('out_of_stock', 'Out Of Stock'), ('pod', 'Print On Demand'),
        ('new_edition', 'New Edition'), ('discontinued', 'Discontinued'),
        ('vendor_change', 'Vendor Change'), ('rights_restricted', 'Rights Restricted'),
        ('bundle_book', 'Bundle Book'), ('market_restricted', 'Market Restricted'),
        ('sale_restricted', 'Sale Restricted'), ('bo', 'Back Order'),
        ('reprinting', 'Reprinting'), ('min_qty_req', 'Minimum Qty/Amount Required'),
        ('vendor_not_found', 'Vendor Not Found'), ('without_budget', 'Without Budget'),
        ('nmc_rest', 'NMC Restriction'),('unavailable', 'Unavailable'),
        ('non_books', 'Non Books'),('oss', 'OOS Delivered'),('replaced', 'Replaced in another Order'),],
                                           copy=False)
    so_qty = fields.Float(string='Quote Qty', default=0)
    so_quantity = fields.Float(string='SO Qty', default=0)
    quote_cancel_qty = fields.Float(string='Quote Cancel Qty', default=0, copy=False)
    cancelled_qty = fields.Float(string='Canceled Qty', default=0, copy=False)

    @api.onchange('so_qty', 'cancelled_qty', 'quote_cancel_qty')
    def onchange_update_so_quantity(self):
        for rec in self:
            # if rec.state in ("draft", "sent", "rejected", "done"):
            rec.so_quantity = rec.so_qty - rec.quote_cancel_qty
            # else:
            #     rec.so_quantity = rec.so_qty - rec.cancelled_qty

    # @api.onchange('so_qty', 'cancelled_qty')
    # def onchange_update_so_quantity(self):
    #     for rec in self:
    #         rec.so_quantity = rec.so_qty - rec.cancelled_qty

    @api.onchange('cancelled_qty')
    def onchange_cancel_qty(self):
        if self.cancelled_qty > 0 and not self.cancel_reason:
            return {'warning': {
                'title': 'Warning!',
                'message': 'Cancel Reason Required!',
                'type': 'danger',  # You can also use 'danger' for an error message
            }}

    @api.onchange('quote_cancel_qty')
    def onchange_quote_cancel_qty(self):
        if self.quote_cancel_qty > 0 and not self.quote_cancel_reason:
            return {'warning': {
                'title': 'Warning!',
                'message': 'Quote Cancel Reason Required!',
                'type': 'danger',
            }}

    @api.onchange('so_quantity', 'cancelled_qty')
    def onchange_product_uom_qty(self):
        self.product_uom_qty = self.so_quantity - self.cancelled_qty

    def _action_launch_stock_rule(self, *, previous_product_uom_qty=False):
        """
        Launch procurement run method. We allow Odoo to create the chain normally
        to avoid 'No Rule Found' errors, but then we cancel the secondary steps
        to force a sequential flow.
        """
        if self.env.context.get("skip_procurement"):
            return True

        # 1. Run standard Odoo procurement (Creates Pick + Ship)
        # We use a context flag to avoid infinite loops if other overrides exist
        res = super(SoLCCl, self.with_context(skip_procurement_cancel=True))._action_launch_stock_rule(previous_product_uom_qty=previous_product_uom_qty)

        # 2. Sequential Handling: Remove the secondary step (Delivery)
        # We unlink it instead of cancelling to avoid 'Scheduled Date' constraints on cancelled transfers.
        # Our custom code in panworld_stock will recreate this after Pick is done.
        for line in self:
            order = line.order_id
            if order.warehouse_id.delivery_steps == 'pick_ship':
                ship_pickings = order.picking_ids.filtered(
                    lambda p: p.state not in ('done', 'cancel') and
                              p.picking_type_id.code == 'outgoing'
                )
                if ship_pickings:
                    # Break the chain links first to allow deletion
                    ship_pickings.move_ids.write({'move_orig_ids': [(5, 0, 0)], 'move_dest_ids': [(5, 0, 0)]})
                    # Unlink the moves and then the picking to break the chain cleanly
                    ship_pickings.move_ids.unlink()
                    ship_pickings.unlink()

        return res

    def action_cancel_so_lines(self):
        self.write({'state': 'cancel'})

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        if self.env.context.get('custom_picking_id'):
            # Optimization: Use pre-calculated moves if available in context
            moves_by_line = self.env.context.get('custom_moves_by_line')
            if moves_by_line and moves_by_line.get(self.id):
                moves = self.env['stock.move'].browse(moves_by_line[self.id])
            else:
                picking_ids = self.env.context['custom_picking_id']
                if not isinstance(picking_ids, list):
                    picking_ids = [picking_ids]
                pickings = self.env['stock.picking'].browse(picking_ids)
                moves = pickings.move_ids.filtered(lambda m: m.sale_line_id.id == self.id and m.state == 'done')

            if moves:
                if any(m.product_id != self.product_id for m in moves):
                    # Kit/Bundle logic: find parent quantity from component moves
                    ratios = []
                    bom_line_ids = moves.mapped('bom_line_id')
                    if bom_line_ids:
                        for bl in bom_line_ids:
                            bl_moves = moves.filtered(lambda m: m.bom_line_id == bl)
                            qty_done = sum(bl_moves.mapped('quantity'))
                            qty_per_parent = bl.product_uom_id._compute_quantity(
                                bl.product_qty / bl.bom_id.product_qty, bl.product_id.uom_id
                            )
                            if qty_per_parent:
                                ratios.append(qty_done / qty_per_parent)
                        
                        # Include 0.0 for components missing from this picking to handle partial kit deliveries correctly
                        all_kit_boms = bom_line_ids.mapped('bom_id')
                        for bom in all_kit_boms:
                            for bl in bom.bom_line_ids.filtered(lambda l: l.product_id.type != 'service'):
                                if bl not in bom_line_ids:
                                    ratios.append(0.0)
                        
                        qty = min(ratios) // 1 if ratios else 0.0
                    else:
                        # Fallback: if no bom_line_id, it might not be a kit or data is inconsistent
                        qty = sum(moves.mapped('quantity'))
                else:
                    qty = sum(moves.mapped('quantity'))
                
                res.update({
                    'quantity': qty,
                })
        return res
