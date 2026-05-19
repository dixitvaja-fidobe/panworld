# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    ship_reference = fields.Char('Ship Reference',related="tracking_number_bill_id.ship_no")
    total_ship_kgs = fields.Float('Total Shipping Charges- Per Kgs',related="tracking_number_bill_id.total_shipping_charges_kgs")
    cons_weight = fields.Float('Consolidated Weight',related="tracking_number_bill_id.consolidated_weight")
    carrier_id = fields.Many2one('delivery.carrier', string="Carrier", compute="_compute_carrier_id")

    @api.depends('invoice_origin', 'partner_id', 'invoice_partner_display_name')
    def _compute_carrier_id(self):
        for move in self:
            pickings = self.env['stock.picking'].sudo().search([('partner_bill_id', '=', move.id)], limit=1)
            move.carrier_id = pickings.carrier_id.id if pickings else False