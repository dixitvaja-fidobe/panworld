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
from odoo.tools import float_is_zero, float_round
from odoo.exceptions import UserError, ValidationError
import datetime
import logging
_logger = logging.getLogger(__name__)

class LandedCostValuationLines(models.Model):
    _name = "landed.cost.valuation.lines"
    _description = "Landed Cost Valuation Lines"
    _rec_name = "cost_id"

    cost_id = fields.Many2one("stock.landed.cost", "Landed Cost", ondelete="cascade")
    product_id = fields.Many2one("product.product", "Product", required=True)
    quantity = fields.Float("Quantity", default=1.0, digits=0, required=True)
    weight = fields.Float("Weight", default=1.0, digits="Stock Weight")
    former_cost = fields.Float("Original Value")
    additional_landed_cost = fields.Float(
        "Additional Landed Cost",
    )
    final_cost = fields.Float("New Value")

    # @api.depends("cost_id.valuation_adjustment_lines")
    # def _compute_additional_landed_cost(self):
    #     # Batch optimization: group adjustments by cost_id and product_id
    #     # to avoid O(N*M) heavy filtering in a loop
    #     costs = self.mapped('cost_id')
    #     adj_data = {}
    #     for cost in costs:
    #         for adj in cost.valuation_adjustment_lines:
    #             key = (cost.id, adj.product_id.id)
    #             adj_data[key] = adj_data.get(key, 0.0) + adj.additional_landed_cost
    #
    #     for rec in self:
    #         rec.additional_landed_cost = adj_data.get((rec.cost_id.id, rec.product_id.id), 0.0)
    #
    # @api.depends("former_cost", "additional_landed_cost")
    # def _compute_final_cost(self):
    #     for rec in self:
    #         rec.final_cost = rec.former_cost + rec.additional_landed_cost


