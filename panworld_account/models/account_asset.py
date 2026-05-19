# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import api, fields, models

class AccountAsset(models.Model):
    """Add Partner for the Deferred expense"""
    _inherit = "account.asset"

    partner_id = fields.Many2one("res.partner", string="Partner", copy=False)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        assets = self.filtered(lambda asset: asset._origin.id and asset.partner_id)
        if not assets:
            return

        moves = self.env['account.move'].search([
            ('asset_id', 'in', assets._origin.ids),
            ('state', '=', 'draft')
        ])
        if moves:
            moves.write({'partner_id': self.partner_id.id})
            moves.mapped('line_ids').write({'partner_id': self.partner_id.id})

