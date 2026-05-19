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



class ResPartner(models.Model):
    _inherit = "res.partner"

    # marketplace_cost = fields.Float(string='Marketplace Cost')
    # other_cost = fields.Float(string='Other Cost')
    pick_type = fields.Selection(
        selection=[
            ("picked_by_customer", "Picked By Customer"),
            ("door_delivery", "Door Delivery"),
        ],
        default="door_delivery",
        string="Shipping Method",
    )
    marketplace_cost_ids = fields.One2many(
        "marketplace.cost.line", "partner_id", string="Marketplace Cost"
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account',
        company_dependent=True)

    def _get_marketplace_other_cost(self, date_order):
        # Get marketplace cost and other cost for sale order and invoice base on date.
        marketplace_cost = 0.0
        other_cost = 0.0
        cost_line_rec = self.marketplace_cost_ids.filtered(
            lambda cost: cost.date <= date_order
        )
        if cost_line_rec:
            marketplace_cost = cost_line_rec[0].marketplace_cost
            other_cost = cost_line_rec[0].other_cost
        return {"marketplace_cost": marketplace_cost, "other_cost": other_cost}


