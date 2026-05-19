# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model_create_multi
    def create(self, vals_list):
        """
        Restrict manual creation of stock quants to users in the 'Allow Stock Quant Creation' group.
        Standard system operations (like move validation) use sudo(), which bypasses this check.
        """
        if not self.env.su and not self.env.user.has_group('panworld_stock.group_allow_physical_adjustment'):
            raise UserError(_("You are not allowed to manually create stock quants. Please contact your administrator."))
        return super(StockQuant, self).create(vals_list)

    def write(self, vals):
        """
        Restrict manual editing of stock quants to users in the 'Allow Stock Quant Creation' group.
        Standard system operations (like move validation) use sudo(), which bypasses this check.
        """
        # Fields that shouldn't be edited by regular users manually
        restricted_fields = ['inventory_quantity', 'inventory_quantity_auto_apply', 'location_id', 'product_id', 'lot_id', 'package_id', 'owner_id']

        if not self.env.su and any(field in vals for field in restricted_fields):
            if not self.env.user.has_group('panworld_stock.group_allow_physical_adjustment'):
                raise UserError(_("You are not allowed to manually edit stock quants. Please contact your administrator."))
        return super(StockQuant, self).write(vals)
