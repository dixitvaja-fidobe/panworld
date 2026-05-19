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


class SaleOrder(models.Model):
    _inherit = "sale.order"

    rma_done = fields.Boolean("RMA is Done", copy=False)
    rma_count = fields.Integer(string="RMA Count", compute="_compute_rma")
    rma_ids = fields.One2many("rma.ret.mer.auth", "sale_order_id", string="RMA")

    @api.depends("rma_ids")
    def _compute_rma(self):
        """ Compute total count of RMA """
        for rma in self:
            rma.rma_count = rma.rma_ids and len(rma.rma_ids.ids) or 0

    def count_rma(self):
        """
            Counting the number of RMA.
            Redirect to RMA Views.
        """
        for rec in self:
            rma_view_id = self.env.ref("scs_rma.exchange_rma_ret_mer_auth_form")
            rma_ids = self.env["rma.ret.mer.auth"].search(
                [("sale_order_id", "=", rec.id)]
            )
            if len(rma_ids.ids) == 1:
                return {
                    "name": "RMA",
                    'views': [(False, 'form')],
                    "res_model": "rma.ret.mer.auth",
                    "type": "ir.actions.act_window",
                    'domain': [('sale_order_id', 'in', rma_ids)],
                    "res_id": rma_ids[0].id,
                    'target': 'current',
                    'context': {'create': False, 'delete': False},
                }

            elif len(rma_ids.ids) > 1:
                return {
                    "name": "RMA",
                    "type": "ir.actions.act_window",
                    "res_model": "rma.ret.mer.auth",
                    "view_mode": "list,form",
                    "domain": [('sale_order_id', '=', self.id)],
                }
