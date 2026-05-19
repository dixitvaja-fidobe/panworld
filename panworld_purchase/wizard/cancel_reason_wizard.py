
from odoo import models, fields, api, exceptions, _


class PickingCancelReason(models.TransientModel):
    _name = 'picking.cancel.reason'
    _description = 'Picking Cancel Reason'

    # TASK - 02908
    cancel_reason = fields.Selection(string="Cancel Reason", selection=[
        ('forthcoming', 'Forthcoming'), ('out_of_print', 'Out Of Print'),
        ('out_of_stock', 'Out Of Stock'), ('print_on_demand', 'Print On Demand'),
        ('new_edition', 'New Edition'), ('discontinued', 'Discontinued'),
        ('vendor_change', 'Vendor Change'), ('rights_restricted', 'Rights Restricted'),
        ('bundle_book', 'Bundle Book'), ('market_restricted', 'Market Restricted'),
        ('sale_restricted', 'Sale Restricted'), ('back_order', 'Back Order'),
        ('delivery_change', 'Delivery Address Changed')],
                                     copy=False, required=True)


    def action_picking_cancel(self):
        active_id = self.env.context.get('active_id')
        picking_id = self.env['stock.picking'].browse(active_id)
        for line in picking_id.move_ids:
            if not line.cancel_reason:
                line.cancel_reason = self.cancel_reason
        picking_id.action_cancel()

