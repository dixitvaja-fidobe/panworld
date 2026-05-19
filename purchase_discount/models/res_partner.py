# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    default_supplierinfo_discount = fields.Float(
        string="Default Supplier Discount (%)",
        digits="Discount",
        help="This value will be used as the default one, for each new"
        " supplierinfo line depending on that supplier.",
        tracking=True,
    )
