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
from odoo.tools import float_is_zero


class StockMove(models.Model):
    _inherit = "stock.move"

    bom_id = fields.Many2one(
        'mrp.bom', 
        string="Parent BOM", 
        related='bom_line_id.bom_id', 
        store=True
    )
    product_barcode = fields.Char(
        related='product_id.barcode', 
        string="Barcode"
    )
