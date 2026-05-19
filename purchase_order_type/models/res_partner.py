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


class ResPartner(models.Model):
    _inherit = "res.partner"

    purchase_type = fields.Many2one(
        comodel_name="purchase.order.type", string="Purchase Order Type"
    )
