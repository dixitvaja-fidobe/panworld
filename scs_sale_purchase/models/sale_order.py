# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import _, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    """Model Sale Order. extended."""
    _inherit = "sale.order"


    def action_view_wiz_sale_purchase(self):
        wiz_view_id = self.env.ref("scs_sale_purchase.view_wiz_sale_purchase_order_form")
        done_po = self.filtered(lambda l: l.purchase_order_count > 0)
        if done_po:
            raise ValidationError(_("Purchase order already exists for Sale Order %s."% ' ,'.join(done_po.mapped('name'))))
        return {
                    "name": "Create Purchase Order",
                    "view_type": "form",
                    "view_mode": "form",
                    "view_id": wiz_view_id.id,
                    "res_model": "wiz.sale.purchase",
                    "type": "ir.actions.act_window",
                    "target": "new",
                }
