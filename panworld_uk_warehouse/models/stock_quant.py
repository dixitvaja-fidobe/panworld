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


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.model
    def _search(self,args,offset=0,limit=None,order=None,**kwargs):
        args = args or []
        ctx = self.env.context or {}
        if ctx.get('uk_warehouse_search_default') and \
            self.env.user.has_group("panworld_uk_warehouse.group_uk_warehouse_user_uk"):
            location_ids = self.env["stock.location"].search([
                ("name", "=", 'Stock'),
                ("location_id.name", "=", 'UKWAR'),
                ("company_id", "in", self.env.companies.ids),
            ])
            args.extend([("location_id", "in", location_ids.ids)])
        return super(StockQuant, self)._search(args,offset=offset,limit=limit,order=order,**kwargs)
