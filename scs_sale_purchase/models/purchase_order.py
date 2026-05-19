# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import _, fields, models


class PurchaseOrderLine(models.Model):
    """Model Sale Order. extended."""
    _inherit = "purchase.order.line"

    sale_reference = fields.Char('Sale Origin')
