# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import _, fields, models
from odoo.osv import expression
from odoo.tools.misc import format_datetime


class StockQuantityHistory(models.TransientModel):
    _inherit = 'stock.quantity.history'

    # Added warehouse filter for the  Uk warehouse
    def open_at_date(self):
        res = super(StockQuantityHistory, self).open_at_date()
        if self.env.user.has_group("panworld_uk_warehouse.group_uk_warehouse_user_uk"):
            tree_view_id = self.env.ref('panworld_uk_warehouse.view_stock_product_tree_uk_warehouse').id
            warehouse_id = self.env['stock.warehouse'].search([
                    ('code', '=', 'UKWAR')
                ], limit=1)
            ctx = res.get('context')
            ctx.update({'warehouse': warehouse_id.id})
            res.update({
                'views':[(tree_view_id, 'tree')],
                        'view_mode': 'tree'})
        return res
