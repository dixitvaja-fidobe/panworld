# See LICENSE file for full copyright and licensing details.

from odoo import models
import datetime
import logging
_logger = logging.getLogger(__name__)

class StockImmediateTransfer(models.TransientModel):
    _inherit = "stock.backorder.confirmation"

    def process(self):
        res = super(StockImmediateTransfer, self).process()
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        backorder_picking_ids = self.env['stock.picking']
        if active_model == 'purchase.order' and active_id:
            backorder_picking_ids = self.env['purchase.order'].browse(active_id).picking_ids.filtered(lambda x: x.backorder_id)
        elif active_model == 'stock.picking' and active_id:
            backorder_picking_ids = self.env['stock.picking'].browse(active_id).purchase_id.picking_ids.filtered(lambda x: x.backorder_id)
        for rec in backorder_picking_ids:
            rec.write({
                'doc_nb_console': False,
                'other_bill_charges': False,
                'ship_no': False,
                'boe_date': False,
                'ready_for_scan_1': False,
                'carrier_id': False,
                'consolidated_weight_shipping': False,
            })
        return res
