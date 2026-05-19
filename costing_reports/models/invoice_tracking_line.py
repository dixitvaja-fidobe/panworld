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


class InvoiceTrackingLine(models.Model):
    _name = "invoice.tracking.line"

    tracking_number_id = fields.Many2one("tracking.number", string="Tracking Number")
    move_id = fields.Many2one("account.move", domain="[('move_type', '=', 'out_invoice')]")
    weight_qty = fields.Float(string="Total Weight-qty", store=True)
    shipping_cost_per_product = fields.Float(string="Shipping Cost Per Product", store=True)
    partner_id = fields.Many2one('res.partner')
    invoice_date = fields.Date(string='Invoice/Bill Date')
    invoice_date_due = fields.Date(string='Due Date')
    weight = fields.Float(string="Weight")
    product_id = fields.Many2one('product.product')







