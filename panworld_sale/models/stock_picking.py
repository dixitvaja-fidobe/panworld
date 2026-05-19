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


class StockPicking(models.Model):
    _inherit = "stock.picking"

    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account')
    division_type_id = fields.Many2one('division.type', string='Division Type')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        # Overwrite method to pass division type and analytic account base on Contact.
        # res = super().onchange_partner_id()
        self.analytic_account_id = self.partner_id.analytic_account_id or False
        self.division_type_id = self.partner_id.division_type_id or False
        # return res

    # @api.onchange('scheduled_date')
    # def _onchange_scheduled_date_tat_brached(self):
    #     if self.scheduled_date:
    #         ship_picking_type_ids = self.env['stock.picking.type'].sudo().search([('sequence_code', '=', 'OUT')]).ids
    #         so_picking = self.search([('picking_type_id', 'in', ship_picking_type_ids), ('sale_id', '=', self.sale_id.id)], order='create_date asc',
    #             limit=1)
    #         if so_picking and self.sale_id.commitment_date and so_picking.scheduled_date.date() > self.sale_id.commitment_date.date():
    #             pass
                # self.env['sales.tracker.report']._trigger_sale_tat_breached(sale_id=self.sale_id.id)