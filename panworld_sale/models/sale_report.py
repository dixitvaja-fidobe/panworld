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


class SaleReport(models.Model):
    _inherit = 'sale.report'

    sales_manager_id = fields.Many2one('hr.employee', string="Sales Manager", readonly=True)

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res['sales_manager_id'] = 's.sales_manager_id'
        return res

    def _group_by_sale(self):
        res = super()._group_by_sale()
        res += ', s.sales_manager_id'
        return res
