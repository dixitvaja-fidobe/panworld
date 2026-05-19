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

class PickingType(models.Model):
    _inherit = "stock.picking.type"

    @api.model
    def _search(
        self,
        args,
        offset=0,
        limit=None,
        order=None,
            **kwargs
    ):
        args = args or []
        if self.env.user.has_group("panworld_uk_warehouse.group_uk_warehouse_user_uk"):
            args.extend([("warehouse_id.code", "=", 'UKWAR')])
        return super(PickingType, self)._search(
            args,
            offset=offset,
            limit=limit,
            order=order,
            **kwargs
        )
