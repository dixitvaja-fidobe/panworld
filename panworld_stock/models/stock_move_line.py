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


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    sale_order_id = fields.Many2one(related='move_id.picking_id.sale_id')
    purchase_order_id = fields.Many2one(related='move_id.picking_id.purchase_id')
    state = fields.Selection(related='move_id.state', store=True, copy=False)