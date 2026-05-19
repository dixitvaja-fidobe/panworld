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
from odoo.tools import float_is_zero, float_round
from odoo.exceptions import UserError, ValidationError
import datetime
import logging
_logger = logging.getLogger(__name__)

class StockLandedCost(models.Model):
    _inherit = "stock.landed.cost"

    weight = fields.Float(string="Total Weight")
    consolidated_weight = fields.Float("Consolidated Weight")
    shipping_cost_bool = fields.Boolean("Shipping Cost Check")
    carrier_tracking_ref = fields.Char(string="Tracking(AWB)")
    delivery_carrier_id = fields.Many2one("delivery.carrier", string="Delivery Method")
    done_quantity = fields.Float(string="Counted Quantity", readonly=1)
    total_of_purchase = fields.Float(
        string="Total of Purchase value",
    )
    landed_cost_valuation_lines = fields.One2many(
        "landed.cost.valuation.lines",
        "cost_id",
        string="Landed Cost Valuation"
    )
    landed_cost_added = fields.Boolean(
        # compute="_compute_landed_cost_added"
    )
    consolidated_amount_total = fields.Monetary(
        "Total",
        # compute="_compute_total_consolidated_amount",
        store=True
    )
    related_bill = fields.Many2many("account.move",
                                    string='Related Bill',
                                    domain=[('move_type', '=', 'in_invoice')]
                                    )
    grn_tracking_number_id = fields.Many2one("tracking.number",
                                             string='Tracking Number')
    tov_value = fields.Float('Total Original Value',
                             # compute="_compute_total_of_purchase",
                             store=True)
    talc_value = fields.Float('Total Additional Landed cost',
                              # compute="_compute_total_of_purchase",
                              store=True)
    differance_tov_talc = fields.Float('Diff of TALC & Addnl Cost',
                                       # compute="_compute_total_of_purchase",
                                       store=True)
    shipping_inward_freight = fields.Float(string="Shipment Inward Freight",
                                           # compute="_compute_shipping_inward_freight"
                                           )
    shipping_clearance_charges = fields.Float(string="Shipment Clearance Charges",
                                              # compute="_compute_shipping_clearance_charges"
                                              )
    picking_count = fields.Integer(compute='_compute_picking_count', string='Pickings')

    partner_id = fields.Many2one('res.partner', string="Partner")
    vendor_currency_id = fields.Many2one('res.currency', string="Vendor Currency")
    amount_total_currency = fields.Monetary(
        string="Total",
        compute="_compute_amount_total_currency",
        currency_field='vendor_currency_id'
    )

    @api.depends('cost_lines.landed_cost', 'vendor_currency_id')
    def _compute_amount_total_currency(self):
        for rec in self:
            rec.amount_total_currency = sum(rec.cost_lines.mapped('landed_cost'))

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.vendor_currency_id = self.partner_id.property_purchase_currency_id or self.partner_id.currency_id

    @api.onchange('vendor_currency_id')
    def _onchange_vendor_currency_id(self):
        for line in self.cost_lines:
            line.onchange_landed_cost()
    invoice_ref = fields.Char(string="Invoice Reference")
    payment_ids = fields.Many2many(
        "account.payment",
        relation="account_payment_landed_cost_rel",
        column1="landed_cost_id",
        column2="payment_id",
        string="Payments",
        copy=False,
    )

    @api.depends('picking_ids')
    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = len(rec.picking_ids)

    def action_view_pickings(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")
        action['domain'] = [('id', 'in', self.picking_ids.ids)]
        return action

    @api.onchange('grn_tracking_number_id')
    def _onchange_grn_tracking_number_id(self):
        if self.grn_tracking_number_id:
            bills = self.env['account.move'].search([
                ('tracking_number_bill_id', '=', self.grn_tracking_number_id.id),
                ('move_type', '=', 'in_invoice')
            ])
            self.related_bill = [(6, 0, bills.ids)]
            self._onchange_related_bill()

    @api.onchange('related_bill')
    def _onchange_related_bill(self):
        if not self.related_bill:
             self.picking_ids = [(6, 0, [])]
             return

        if self.related_bill:
            company_id = self.company_id.id or self.env.company.id
            pickings = self.env['stock.picking'].search([
                ('partner_bill_id', 'in', self.related_bill.ids),
                ('state', '=', 'done'),
                ('picking_type_id.code', '=', 'incoming'),
                ('company_id', '=', company_id)
            ])
            self.picking_ids = [(6, 0, pickings.ids)]


    def action_view_account_move(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Journal Entry',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.account_move_id.id,
        }

    def reset_to_draft(self):
        self.state = "draft"
        self.account_move_id.button_draft()

    is_payment_paid = fields.Boolean("Is Payment Paid", compute='_compute_is_payment_paid', store=True)
    payment_status = fields.Selection(
        [('paid', 'Paid'), ('not_paid', 'Not Paid')],
        string="Payment Status",
        compute='_compute_payment_status',
        store=True,
        default='not_paid'
    )

    @api.depends('payment_ids', 'payment_ids.state')
    def _compute_is_payment_paid(self):
        for rec in self:
            rec.is_payment_paid = any(p.state in ('posted', 'reconciled') for p in rec.payment_ids)

    @api.depends('is_payment_paid')
    def _compute_payment_status(self):
        for rec in self:
            if rec.is_payment_paid:
                rec.payment_status = 'paid'
            else:
                rec.payment_status = 'not_paid'

    payment_count = fields.Integer(compute='_compute_payment_count', string='Payment Count')

    @api.depends('payment_ids')
    def _compute_payment_count(self):
        for rec in self:
            rec.payment_count = len(rec.payment_ids)

    def action_view_payments(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_payments")
        action['domain'] = [('id', 'in', self.payment_ids.ids)]
        action['context'] = {'default_landed_cost_ids': [(6, 0, self.ids)]}
        return action

    def compute_landed_cost(self):
        res = super(StockLandedCost, self).compute_landed_cost()
        self.done_quantity = sum(
            self.picking_ids.mapped("total_done_qty")
        )
        return res

    def action_mass_post(self):
        for rec in self:
            if rec.state == 'draft':
                rec.button_validate()


class StockValuationAdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'

    def _prepare_account_move_line_values(self):
        res = super()._prepare_account_move_line_values()
        if self.cost_id.partner_id:
            res['partner_id'] = self.cost_id.partner_id.id
        return res

    def _create_account_move_line(self, credit_account_id, debit_account_id, remaining_qty):
        """ Always use the full quantity to ensure no lines are missed and the full value is posted,
            even if the item is no longer in stock.
        """
        return super()._create_account_move_line(credit_account_id, debit_account_id, self.quantity)
