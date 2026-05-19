# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MarketplaceCostLine(models.Model):
    _name = "marketplace.cost.line"
    _description = "Marketplace Cost Line"
    _order = "date desc"

    partner_id = fields.Many2one("res.partner", string="Customer")
    date = fields.Date(
        string="Date",
        help="Set date for marketplace cost and other cost to \
        used in sale order and invoice",
    )
    marketplace_cost = fields.Float(
        string="Marketplace Cost (%)",
        help="Set marketplace cost to used in sale \
        order and invoice base on order / invoice date",
    )
    other_cost = fields.Float(
        string="Other Cost (%)",
        help="Set other cost to used in sale \
        order and invoice base on order / invoice date",
    )
    salesman_commission = fields.Float(
        string="Salesman Commission (%)",
    )
    other_commission = fields.Float(
        string="Other Commission (%)",
    )



    @api.constrains("date")
    def _check_date(self):
        # Set validation on same date in marketplace and other cost.
        for rec in self:
            cost_line_rec = rec.search(
                [
                    ("partner_id", "=", rec.partner_id.id),
                    ("id", "!=", rec.id),
                    ("date", "=", rec.date),
                ],
                limit=1,
            )
            if cost_line_rec:
                raise ValidationError(
                    _("You can not add same date in marketplace and other cost!")
                )