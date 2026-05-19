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

class ResCompnay(models.Model):
    _inherit = 'res.company'

    def _get_sale_tracker_domain(self):
        return [('model_id', '=', self.env.ref('panworld_sale_tracker.model_sales_tracker_report').id),
                ('ttype', '=', 'float')]

    sale_tracker_warehouse_fields = fields.Many2many(
        comodel_name='ir.model.fields',
        domain=_get_sale_tracker_domain,
        string='Sale Tracker Warehouse Fields')
