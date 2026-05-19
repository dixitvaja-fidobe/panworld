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


class ResCompany(models.Model):
    """inherited data model of ResCompany to add Locations."""

    _inherit = "res.company"

    source_location_id = fields.Many2one("stock.location", string="Source Location", domain="[('company_id', '=', id)]")
    destination_location_id = fields.Many2one(
        "stock.location", string="Destination Location", domain="[('company_id', '=', id)]"
    )
    sup_source_location_id = fields.Many2one(
        "stock.location", string="Source Location", domain="[('company_id', '=', id)]"
    )
    sup_destination_location_id = fields.Many2one(
        "stock.location", string="Destination Location", domain="[('company_id', '=', id)]"
    )
