# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_imported = fields.Boolean(
        string="Is imported?", help="Import sale order from sheet"
    )
