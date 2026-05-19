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


class PurchaseRequest(models.Model):

    _inherit = "purchase.request"

    customer_sales_order = fields.Char(string='Customer Sales Order')
    customer_so_date = fields.Date(string='Customer Sales Order Date')
    expected_material_received_date = fields.Date(string='Expected material received date')
    expected_order_dispatch_date = fields.Date(string='Expected order dispatch date')
    request_for_customer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Request For Customer",
    )

    @api.depends("line_ids")
    def _compute_move_count(self):
        """Fixed the issue of count in picking"""
        for rec in self:
            rec.move_count = len(
                rec.mapped(
                    "line_ids.purchase_request_allocation_ids.stock_move_id.picking_id"
                )
            )


class PurchaseRequestLine(models.Model):

    _inherit = "purchase.request.line"

    customer_sales_order = fields.Char(
        related="request_id.customer_sales_order", string="Customer Sales Order", store=True
    )
