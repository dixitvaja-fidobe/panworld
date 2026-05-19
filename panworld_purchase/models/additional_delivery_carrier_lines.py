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


class AdditionalDeliveryCarrierLines(models.Model):
    _name = "additional.delivery.carrier.lines"
    _description = "Additional Delivery Carrier Lines"
    _inherit = ["additional.services"]

    carrier_id = fields.Many2one(
        "delivery.carrier", string="Carrier", copy=False, ondelete="cascade"
    )