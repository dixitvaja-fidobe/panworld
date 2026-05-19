# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        # Update picking invoice state.
        vals = super()._prepare_invoice()
        for picking in self.picking_ids.filtered(lambda p: p.state == 'done'):
            for move in picking.move_line_ids:
                if move.picking_id.invoice_state == "2binvoiced":
                    if (move.state != "cancel") and not picking.has_scrap_move:
                        picking.write({
                            'invoice_state': 'invoiced'
                        })
        return vals