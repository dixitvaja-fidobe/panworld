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

# class ResCompnay(models.Model):
#     _inherit = 'res.company'
#
#     picking_type_ids = fields.Many2many('stock.picking.type', string="Picking Type",check_company=True,)
#
#     def _get_sale_tracker_domain(self):
#         return [('model_id', '=', self.env.ref('panworld_sale.model_sales_tracker_report').id),
#                 ('ttype', '=', 'float')]
#
#     sale_tracker_warehouse_fields = fields.Many2many(
#         comodel_name='ir.model.fields',
#         domain=_get_sale_tracker_domain,
#         string='Sale Tracker Warehouse Fields')


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    sale_tracker_report_code = fields.Char(string='Sale Tracker Report Code')
