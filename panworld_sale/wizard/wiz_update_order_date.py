# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import fields, models


class UpdateOrderDate(models.TransientModel):
    """Wiz Sale Purchase TransientModel ."""

    _name = "wiz.update.order.date"
    _description = "Update Order Date"

    order_date = fields.Datetime(string='Order Date')

    def action_update_order_dare(self):
        """Button method to update order date."""
        active_model = self.env.context.get("active_model")
        if active_model and active_model == 'sale.order':
            sale_rec = self.env[active_model].browse(
                self.env.context["active_ids"]
            )
            sale_rec.write({'date_order': self.order_date})
