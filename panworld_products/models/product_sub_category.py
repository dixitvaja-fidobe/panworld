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


class ProductSubCategory(models.Model):
    _name = "product.sub.category"
    _description = "Product Sub Category"

    name = fields.Char(required=True)
