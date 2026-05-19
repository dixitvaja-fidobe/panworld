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

    picking_type_ids = fields.Many2many('stock.picking.type', string="Picking Type",check_company=True,)

