# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_product_info_pos(self, price, quantity, pos_config_id):
        res = super(ProductProduct, self).get_product_info_pos(price, quantity, pos_config_id)
        config = self.env['pos.config'].browse(pos_config_id)
        picking_type = config.picking_type_id
        qty_available = 0
        location_name = ""
        if picking_type and picking_type.default_location_src_id:
            source_location_id = picking_type.default_location_src_id
            location_name = source_location_id.display_name
            qty_available = self.env['stock.quant']._get_available_quantity(self, source_location_id)
        res.update({
            'qty_available': qty_available,
            'uom_name': self.uom_name,
            'location_name': location_name
        })
        return res


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_product_accounts(self):
        # Override this method to set product account base on Sales Journal
        context = self.env.context or {}
        if context.get('is_pos_session_id'):
            pos_config_rec = self.env['pos.config'].browse(context.get('is_pos_session_id'))
            if pos_config_rec and pos_config_rec.journal_id:
                accounts = super(ProductTemplate, self)._get_product_accounts()
                accounts.update({
                    'income': pos_config_rec.journal_id.default_account_id
                })
                return accounts
        return super()._get_product_accounts()
