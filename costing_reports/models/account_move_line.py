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


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tracking_number_id = fields.Many2one("tracking.number", related='move_id.tracking_number_id', string="Tracking Number", domain="[('move_id.move_type', '=', 'out_invoice')]" )
    bill_tracking_number_id = fields.Many2one("tracking.number", string="Tracking Number", store=True)
    journal_tracking_number_id = fields.Many2one("tracking.number", string="Tracking Number")
    weight_qty = fields.Float(string="Total Weight-qty", compute="_compute_weight_qty", store=True)
    shipping_cost_per_product = fields.Float(string="Shipping Cost Per Product", compute="_compute_weight_qty", store=True)

    # partner_id = fields.Many2one('res.partner', related="move_id.partner_id", store=True)
    partner_id = fields.Many2one('res.partner', store=True)
    invoice_date = fields.Date(string='Invoice/Bill Date', related="move_id.invoice_date")
    invoice_date_due = fields.Date(string='Due Date', related="move_id.invoice_date_due")
    product_weight = fields.Float(related="product_id.weight", string="Weight")
    tracking_journal_item_flag = fields.Boolean(string="Tracking Journal Flag", default=False)
    move_type = fields.Selection(selection=[
            ('entry', 'Journal Entry'),
            ('out_invoice', 'Customer Invoice'),
            ('out_refund', 'Customer Credit Note'),
            ('in_invoice', 'Vendor Bill'),
            ('in_refund', 'Vendor Credit Note'),
            ('out_receipt', 'Sales Receipt'),
            ('in_receipt', 'Purchase Receipt'),
        ], string='Type', related="move_id.move_type")

    @api.depends('quantity', 'product_id', 'product_id.weight', 'tracking_number_id', 'tracking_number_id.inv_cost_weight', 'tracking_number_id.bill_cost_weight')
    def _compute_weight_qty(self):
        for rec in self:
            weight_qty = rec.product_id.weight * rec.quantity
            rec.weight_qty = weight_qty
            if rec.move_id.move_type == 'out_invoice':
                rec.shipping_cost_per_product = rec.tracking_number_id.inv_cost_weight * weight_qty
            elif rec.move_id.move_type == 'in_invoice':
                rec.shipping_cost_per_product = rec.bill_tracking_number_id.bill_cost_weight * weight_qty
            else:
                rec.shipping_cost_per_product = 0.0

    @api.onchange('account_id', 'debit')
    def _onchange_account_id_to_tracking_required(self):
        if self.move_id.move_type == 'entry':
            if self.account_id.code in ['501501', '503101'] and self.debit > 0.0:
                self.update({'tracking_journal_item_flag': True})
            else:
                self.update({'tracking_journal_item_flag': False})