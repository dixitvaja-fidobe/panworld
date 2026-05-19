# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################import logging
import logging
_logger = logging.getLogger(__name__)
from odoo import api, fields, models, _


class SoCCl(models.Model):
    _inherit = 'sale.order'

    def _create_diff_backorder_picking(self, lines_backorder, action_backorder=False):
        lines_backorder.with_context(is_backorder=True)._action_launch_stock_rule()
        lines_backorder._compute_qty_delivered()

    # @api.onchange('order_line.cancelled_qty')
    # def onchang_cancel_qty(self):
    #     if self.order_line:
    #         self.order_line.check_cancel_qty()

    def _get_invoiceable_lines(self, final=False):
        """Return the invoiceable lines for order `self`."""
        if self.env.context.get('custom_picking_id'):
            picking_id = self.env['stock.picking'].browse(self.env.context.get('custom_picking_id'))
            invoiceable_line_ids = picking_id.move_ids.mapped('sale_line_id').ids
            return self.env['sale.order.line'].browse(invoiceable_line_ids)
        else:
            return super()._get_invoiceable_lines(final=final)


