# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import _, fields, models, api
from odoo.exceptions import ValidationError
import re


class TrackingNumber(models.Model):
    _name = "tracking.number"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Costing Reports"
    _rec_name = 'name'

    name = fields.Char()
    total_inv_weight = fields.Float(string="Total Inv Weight", compute="_compute_cost", store=True)
    inv_cost_weight = fields.Float(string="Cost/Weight", compute="_compute_cost", store=True)
    total_bill_weight = fields.Float(string="Total Bill Weight", compute="_compute_cost", store=True)
    bill_cost_weight = fields.Float(string="Cost/Weight", compute="_compute_cost", store=True)
    invoice_line_ids = fields.One2many("account.move.line", 'tracking_number_id', string="Invoices", domain=[('move_type', '=', 'out_invoice')])
    bill_line_ids = fields.One2many("account.move.line", 'bill_tracking_number_id', string="Bills", domain=[('move_id.is_shipping_service', '!=', True), ('move_type', '=', 'in_invoice')])
    journal_line_ids = fields.One2many("account.move.line", 'journal_tracking_number_id', string="Journals", domain=[('move_type', '=', 'entry')])
    cost = fields.Float(string="Cost", compute="_compute_cost", store=True)
    total_debit_amount = fields.Float(string="Total Debit Amount", compute="_compute_cost", store=True)

    invoice_tracking_count = fields.Integer(string="Invoices Count", compute="_compute_invoices")
    consolidated_weight = fields.Float(string="Consolidated Weight")
    ship_no = fields.Char(string="Ship No.")
    boe_no = fields.Char(string="BOE No.")
    boe_date = fields.Date(string="BOE Date")
    ready_to_scan = fields.Char(string="Ready to Scan")

    shipping_inward_total = fields.Float(string="Shipment Inward Freight- Total")
    shipping_clearance_total = fields.Float(string="Shipment Clearance Charges- Total")
    weight_comparison = fields.Integer(string="Weight Comparison Factor with Odoo %")
    shipping_inward_kgs = fields.Float(string="Shipment Inward Freight- Per Kgs", compute="_compute_shipping_inward_kgs")
    shipping_clearance_kgs = fields.Float(string="Shipment Clearance Charges- Per Kgs", compute="_compute_shipping_clearance_kgs")
    total_shipping_charges_kgs = fields.Float(string="Total Shipping Charges- Per Kgs", compute="_compute_total_shipping_charges_kgs")

    @api.depends('shipping_inward_kgs', 'shipping_clearance_kgs')
    def _compute_total_shipping_charges_kgs(self):
        self.total_shipping_charges_kgs = 0.0
        for rec in self:
            if rec.shipping_inward_kgs and rec.shipping_clearance_kgs:
                total_shipping_charges = (rec.shipping_inward_kgs + rec.shipping_clearance_kgs)
                rec.total_shipping_charges_kgs = total_shipping_charges

    @api.depends('shipping_inward_total', 'weight_comparison', 'consolidated_weight')
    def _compute_shipping_inward_kgs(self):
        self.shipping_inward_kgs = 0.0
        for rec in self:
            if rec.shipping_inward_total and rec.weight_comparison:
                total_shipping_inward = ((rec.shipping_inward_total/rec.consolidated_weight)*rec.weight_comparison/100)
                rec.shipping_inward_kgs = total_shipping_inward

    @api.depends('shipping_clearance_total', 'weight_comparison', 'consolidated_weight')
    def _compute_shipping_clearance_kgs(self):
        self.shipping_clearance_kgs = 0.0
        for rec in self:
            if rec.shipping_clearance_total and rec.weight_comparison:
                total_shipping_clearance = ((rec.shipping_clearance_total/rec.consolidated_weight)*rec.weight_comparison/100)
                rec.shipping_clearance_kgs = total_shipping_clearance

    @api.depends("invoice_line_ids")
    def _compute_invoices(self):
        """ Compute total count of RMA """
        for line in self:
            line.invoice_tracking_count = line.invoice_line_ids and len(line.invoice_line_ids.ids) or 0

    def count_grn_tracking_invoices(self):
        for rec in self:
            invoice_view_id = self.env.ref("account.view_move_line_tree")
            invoice_line_ids = self.env["account.move.line"].search(
                [("tracking_number_id", "=", rec.id)]
            )
            return {
                "name": "Invoices",
                "view_type": "form",
                "view_mode": "list,form",
                "view_id": False,
                "res_model": "account.move.line",
                "type": "ir.actions.act_window",
                "target": "current",
                "domain": [("id", "in", invoice_line_ids.ids)],
            }

    @api.depends('invoice_line_ids', 'bill_line_ids', 'journal_line_ids')
    def _compute_cost(self):
        for rec in self:
            total_weight = 0.0
            total_bill_weight = 0.0
            for line in rec.invoice_line_ids:
                total_weight += line.product_id.weight * line.quantity
            rec.total_inv_weight = total_weight
            for line in rec.bill_line_ids:
                total_bill_weight += line.product_id.weight * line.quantity
            rec.total_bill_weight = total_bill_weight
            shipping_service = self.env['account.move.line'].search(
                [('move_id.is_shipping_service', '=', True), ('bill_tracking_number_id', '=', rec.id),
                 ('journal_id.shipping_bill', '=', True)])
            cost = sum(shipping_service.mapped('price_subtotal'))
            rec.cost = cost
            rec.inv_cost_weight = cost / rec.total_inv_weight if rec.total_inv_weight > 0 else 1 if rec.total_inv_weight > 0 else 0
            rec.bill_cost_weight = cost / rec.total_bill_weight if rec.total_bill_weight > 0 else 1 if rec.total_bill_weight > 0 else 0
            rec.total_debit_amount = sum(rec.journal_line_ids.mapped('debit')) if rec.journal_line_ids else 0

    @api.constrains('name')
    def _check_tracking_name(self):
        special_characters = r'[@#$%^&*()]'
        for record in self:
            if record.name and record.name.startswith('0') or record.name and ' ' in record.name or record.name and re.search(special_characters, record.name):
                raise ValidationError(
                    _("Tracking Number should not start with 0, should not contain spaces, and should not include special characters like [@#$%^&*()]."))

    @api.model
    def create(self, values):
        if 'name' in values:
            self._check_tracking_name()
            if self.search([('name', '=', values['name'])], limit=1):
                raise ValidationError(_('This tracking number already exists.'))
        return super(TrackingNumber, self).create(values)

    def write(self, values):
        if values.get('name'):
            self._check_tracking_name()
            if self.search([('name', '=', values['name']), ('id', '!=', self.id)], limit=1):
                raise ValidationError(_('This tracking number already exists.'))
        return super(TrackingNumber, self).write(values)
