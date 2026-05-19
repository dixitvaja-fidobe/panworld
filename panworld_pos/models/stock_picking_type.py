# -*- coding: utf-8 -*-
from odoo import fields, models, api

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    allow_negative_stock = fields.Boolean(string='Allow Negative Stock', default=False)

    @api.model
    def _load_pos_data_fields(self, config):
        fields = super()._load_pos_data_fields(config)
        fields.append('allow_negative_stock')
        return fields
