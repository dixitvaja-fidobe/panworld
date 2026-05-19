# -*- coding: utf-8 -*-

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    fs_sale_order_id = fields.Many2one(
        'sale.order',
        string='Tracking Sale Order',
        help="Sale order linked for tracking purposes. "
             "Set automatically from requisition or manually for direct tracking.")

