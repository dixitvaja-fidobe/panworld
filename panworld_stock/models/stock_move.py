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


class StockMove(models.Model):
    _inherit = "stock.move"

    purchase_order_id = fields.Many2one("purchase.order", string="Purchase Order")
    remarks = fields.Char(string='Remarks', help='Text description')
    availability_qty = fields.Float("On Hand", related="product_id.qty_available")
    cancel_reason = fields.Selection(string="Cancel Reason", selection=[
        ('forthcoming', 'Forthcoming'), ('out_of_print', 'Out Of Print'),
        ('out_of_stock', 'Out Of Stock'), ('print_on_demand', 'Print On Demand'),
        ('new_edition', 'New Edition'), ('discontinued', 'Discontinued'),
        ('vendor_change', 'Vendor Change'), ('rights_restricted', 'Rights Restricted'),
        ('bundle_book', 'Bundle Book'), ('market_restricted', 'Market Restricted'),
        ('sale_restricted', 'Sale Restricted'), ('back_order', 'Back Order'),
        ('reprinting', 'Reprinting'), ('minimum_qty_amount_required', 'Minimum Qty/Amount Required'),
        ('delivery_change', 'Delivery Address Changed')], copy=False)
    pending_reason = fields.Selection(string="Pending Reason", selection=[
        ('rfq_requested', 'RFQ Requested'), ('in_transit', 'In Transit'),
        ('out_of_print', 'Out Of Print'),
        ('new_edition', 'New Edition'),
        ('received', 'Received'),
    ], copy=False)
    is_backorder_picking = fields.Boolean(
        string="Is Backorder Picking",
        compute="_compute_is_backorder_picking",
        store=True,
    )
    sml_done_qty = fields.Float(string="Done Qty", compute="_compute_sml_done_qty", store=True)

    @api.depends('move_line_ids.quantity', 'move_line_ids.product_uom_id', 'move_line_ids.picked')
    def _compute_sml_done_qty(self):
        """ Compute the sum of 'Done' quantity from picked move lines.
        This field only sums quantities where picked=True (scanned).
        """
        for move in self:
            move.sml_done_qty = sum(ml.product_uom_id._compute_quantity(ml.quantity, move.product_uom, round=False)
                                   for ml in move.move_line_ids if ml.picked)

    @api.depends('picking_id.backorder_id')
    def _compute_is_backorder_picking(self):
        for move in self:
            move.is_backorder_picking = bool(move.picking_id.backorder_id)
