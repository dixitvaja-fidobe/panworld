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


class StockLocation(models.Model):
    _inherit = "stock.location"

    is_shipper_location = fields.Boolean(string="Is Shipper Location")