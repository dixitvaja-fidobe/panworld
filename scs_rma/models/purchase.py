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


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    rma_done = fields.Boolean("RMA is Done", copy=False)
    rma_count = fields.Integer(string="RMA Count", compute="_compute_rma")
    rma_ids = fields.One2many("rma.ret.mer.auth", "purchase_order_id", string="RMA")

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
        self.ensure_one()

        rma_ids = self.env["rma.ret.mer.auth"].search(
            [("purchase_order_id", "=", self.id)]
        )

        if not rma_ids:
            return False

        if len(rma_ids) == 1:
            return {
                "name": "RMA",
                "type": "ir.actions.act_window",
                "res_model": "rma.ret.mer.auth",
                "view_mode": "form",
                "res_id": rma_ids.id,
                "target": "current",
            }

        return {
            "name": "RMAs",
            "type": "ir.actions.act_window",
            "res_model": "rma.ret.mer.auth",
            "view_mode": "list,form",
            "domain": [("id", "in", rma_ids.ids)],
            "target": "current",
        }

