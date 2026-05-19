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


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def _search(
        self,
        args,
        offset=0,
        limit=None,
        order=None,
    ):
        args = args or []
        if self.env.user.has_group("panworld_uk_warehouse.group_uk_warehouse_user_uk"):
            args.extend([("picking_type_id.warehouse_id.code", "=", 'UKWAR')])
        return super(StockPicking, self)._search(
            args,
            offset=offset,
            limit=limit,
            order=order,
        )