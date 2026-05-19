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


# class StockValuationLayer(models.Model):
#     _inherit = "stock.valuation.layer"

    # @api.model
    # def create(self, vals):
    #     svl = super(StockValuationLayer, self).create(vals)
    #     if svl.stock_move_id and svl.stock_move_id.purchase_line_id \
    #         and svl.stock_move_id.purchase_line_id.product_id.id != svl.stock_move_id.product_id.id \
    #         and svl.stock_move_id.purchase_line_id.product_id.is_kits and not svl.stock_landed_cost_id:
    #         svl.write({'unit_cost': svl.stock_move_id.price_unit, 'value': svl.stock_move_id.price_unit * svl.quantity})
    #     return svl
