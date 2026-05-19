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

class DivisionType(models.Model):
    _name = "division.type"
    _description = "DivisionType"

    name = fields.Char("Division Type")
    sale_tat = fields.Float("Sales TAT")
    purchase_tat = fields.Float("Purchase TAT")
    shipping_tat = fields.Float("Shipping TAT")
    wh_tat = fields.Float("WH TAT")
    delivery_tat = fields.Float("Delivery TAT")
    po_tat = fields.Float("PO TAT")