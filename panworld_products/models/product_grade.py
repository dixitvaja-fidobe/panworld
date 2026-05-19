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


class ProductGrade(models.Model):
    _name = 'product.grade'
    _rec_name = 'name'
    _description = 'Product Grade'

    name = fields.Char()