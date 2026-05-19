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
from odoo.tools import float_round


class AccountMove(models.Model):
    _inherit = "account.move"

    # def _get_customer_related_invoice(self):
    #     domain= [('partner_id', '=', self.partner_id.id)]
    #     return domain

    tracking_number_id = fields.Many2one("tracking.number")
    tracking_number_bill_id = fields.Many2one('tracking.number')
    is_shipping_service = fields.Boolean(
        string="Shipping Service", help="To filtered shipping service record.")

    related_invoice_id = fields.Many2one('account.move', string='Related Invoice')
    value_as_per_bill = fields.Monetary("Value as per Vendor Bill")

    bill_difference_amount = fields.Float(
        compute="_compute_bill_difference_amount", string="Difference", store=True
    )
    total_quantity = fields.Integer(
        compute="_compute_total_quantity", string='Total Quantity', store=True)

    @api.depends("value_as_per_bill", "amount_total")
    def _compute_bill_difference_amount(self):
        for rec in self:
            rec.bill_difference_amount = (
                        float_round(rec.value_as_per_bill, precision_digits=2) - float_round(rec.amount_total,
                                                                                             precision_digits=2))

    @api.depends('invoice_line_ids.quantity')
    def _compute_total_quantity(self):
        # Set default value first
        for move in self:
            move.total_quantity = 0.0
        if not self.ids:
            return
        # Use SQL query for better performance with large datasets
        self.env.cr.execute("""
            SELECT move_id, SUM(quantity) as total_qty
            FROM account_move_line
            WHERE move_id IN %s
            GROUP BY move_id
        """, (tuple(self.ids),))
        results = dict(self.env.cr.fetchall())
        for move in self:
            move.total_quantity = results.get(move.id, 0.0)

    def action_bill_difference_amount(self):
        ctx = dict(self.env.context) or {}
        view_id = self.env.ref("panworld_bill_variance.bill_variance_view_form").id
        ctx.update(
            {"acount_move_active_id": self.id, "acount_move_active_model": self._name}
        )
        return {
            "name": "Add Difference Amount",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "bill.variance",
            "view_id": view_id,
            "views": [(view_id, "form")],
            "target": "new",
            "context": ctx,
        }

    @api.onchange('partner_id', 'related_invoice_id')
    def _get_customer_related_invoice(self):
        return {'domain': {'related_invoice_id': [('partner_id', '=', self.partner_id.id), ('move_type', '=', 'out_invoice')]}}

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountMove, self).create(vals_list)
        for vals in vals_list:
            invoice_line_vals = vals.get('invoice_line_ids')
            if invoice_line_vals:
                track_ids = [line[2].get('bill_tracking_number_id') for line in invoice_line_vals if
                             line[2].get('bill_tracking_number_id')]
                if track_ids:
                    track_records = self.env['tracking.number'].browse(track_ids)
                    for line_vals, line in zip(invoice_line_vals, res.invoice_line_ids):
                        line_data = line_vals[2]
                        track_id = line_data.get('bill_tracking_number_id')
                        if track_id:
                            track_record = track_records.filtered(lambda r: r.id == track_id)
                            if len(track_record) > 1:
                                track_record = track_record[0]
                            line.bill_tracking_number_id = track_record
        return res

    def write(self, vals):
        invoice_line_vals = vals.get('invoice_line_ids')
        res = super(AccountMove, self).write(vals)
        if invoice_line_vals:
            for move in self:
                for line_vals in invoice_line_vals:
                    if isinstance(line_vals, list) and len(line_vals) > 1:
                        operation = line_vals[0]
                        line_id = line_vals[1] if len(line_vals) > 1 else None
                        line_data = line_vals[2] if len(line_vals) > 2 else {}
                        if operation in [0, 1] and line_data:
                            track_id = line_data.get("bill_tracking_number_id")
                            if track_id:
                                tracking_number = self.env["tracking.number"].browse(track_id)
                                if operation == 1 and line_id:
                                    line = self.env["account.move.line"].browse(line_id)
                                    if line and tracking_number:
                                        line.write({"bill_tracking_number_id": tracking_number.id})
                                elif operation == 0:
                                    matching_line = move.invoice_line_ids.filtered(
                                        lambda l: not l.bill_tracking_number_id and
                                        l.product_id.id == line_data.get("product_id")
                                    )
                                    if matching_line and tracking_number:
                                        matching_line[0].write({"bill_tracking_number_id": tracking_number.id})
        return res
