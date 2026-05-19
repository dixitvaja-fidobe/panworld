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


class StockMove(models.Model):
    _inherit = "stock.move"

    customer_name = fields.Char(
        string='Customer Name', related='purchase_line_id.related_so.partner_id.name', help='Customer Name')
    customer_sales_order = fields.Char(string='Customer Sales Order', compute='_compute_customer_sales_order', help='Customer Sales Order')

    @api.depends('purchase_line_id.related_so')
    def _compute_customer_sales_order(self):
        for record in self:
            related_so = record.purchase_line_id.related_so
            record.customer_sales_order = related_so.customer_sales_order if related_so.customer_sales_order else False

