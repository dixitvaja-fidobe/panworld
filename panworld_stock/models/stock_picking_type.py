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

    is_merge_operation = fields.Boolean(string="Merge Operation", default=True)
    is_consolidated_picking = fields.Boolean(string="Consolidated Picking")

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, **kwargs):
        domain = domain or []
        context = self.env.context or {}
        if context.get("is_action_multi_grn"):
            domain.extend([("is_consolidated_picking", "=", True)])
        return super(PickingType, self)._search(
            domain,
            offset=offset,
            limit=limit,
            order=order,
            **kwargs
        )