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

class ProductSubtitle(models.Model):
    _name = 'product.subtitle'
    _rec_name = 'name'
    _description = 'Product Subtitle'

    name = fields.Char()