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


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends('invoice_line_ids', 'invoice_line_ids.move_line_ids')
    def _compute_picking_ids(self):
        """ 
        Enhanced to also link picking from stock valuation layers/moves
        """
        super(AccountMove, self)._compute_picking_ids()
        # If there are other custom ways the link is established, they can be added here.
        # But the standard Many2many in account_move.py already uses invoice_line_ids.move_line_ids.


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # account_move_id = fields.Many2one(
    #     'account.move', string='Stock Journal Entry',
    #     compute='_compute_account_move_id', store=True,
    #     help="The journal entry created corresponding to the stock valuation of this picking."
    # )
    #
    # @api.depends('move_ids', 'move_ids.invoice_line_ids', 'move_ids.invoice_line_ids.move_id')
    # def _compute_account_move_id(self):
    #     for picking in self:
    #         # Search for the journal entry linked to this picking.
    #         # We filter by move_type='entry' to distinguish from Invoices/Bills.
    #         move = self.env['account.move'].sudo().search([
    #             ('picking_ids', 'in', picking.ids),
    #             ('move_type', '=', 'entry')
    #         ], order='id asc', limit=1)
    #         picking.account_move_id = move
