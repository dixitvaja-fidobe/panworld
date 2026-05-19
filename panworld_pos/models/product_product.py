# -*- coding: utf-8 -*-
from odoo import api, models, _

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def _load_pos_data_read(self, records, config):
        # Use super to read standard fields first
        return super()._load_pos_data_read(records, config)
