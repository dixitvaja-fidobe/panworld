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

class StockLandedCostLines(models.Model):
    _inherit = "stock.landed.cost.lines"

    consolidated_cost = fields.Monetary("Cost in AED")
    landed_cost = fields.Monetary("Landed Cost", currency_field='vendor_currency_id')
    vendor_currency_id = fields.Many2one('res.currency', related='cost_id.vendor_currency_id', string="Vendor Currency")
    compute_check_bool = fields.Boolean()

    @api.onchange('landed_cost', 'vendor_currency_id')
    def onchange_landed_cost(self):
        if self.landed_cost and self.vendor_currency_id:
            company_currency = self.env.company.currency_id
            # Convert landed_cost from vendor_currency_id to company_currency (AED)
            converted_cost = self.vendor_currency_id._convert(
                self.landed_cost, company_currency, self.env.company, fields.Date.today()
            )
            self.consolidated_cost = converted_cost
            self.price_unit = converted_cost

    @api.onchange('split_method')
    def _onchange_check_bool(self):
        for rec in self:
            rec.compute_check_bool = True


    @api.onchange('product_id')
    def onchange_product_id(self):
        super(StockLandedCostLines, self).onchange_product_id()
        self.consolidated_cost = self.product_id.standard_price or 0.0

    @api.onchange('consolidated_cost')
    def onchange_consolidated_cost(self):
        # Update standard price_unit whenever our AED cost changes
        self.price_unit = self.consolidated_cost or 0.0



