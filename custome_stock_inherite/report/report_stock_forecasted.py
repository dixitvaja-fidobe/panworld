# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################

from collections import defaultdict

from odoo import api, models
from odoo.tools import float_compare, float_is_zero, format_date, float_round



class ReplenishmentReport(models.AbstractModel):
    _name = 'stock.forecasted_product_product'
    _description = "Stock Replenishment Report"
    _inherit = 'stock.forecasted_product_product'



