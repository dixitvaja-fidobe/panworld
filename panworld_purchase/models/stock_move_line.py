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


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    customer_name = fields.Char(related='move_id.customer_name')
    customer_sales_order = fields.Char(related='move_id.customer_sales_order')