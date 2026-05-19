# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        # Add panworld custom fields values in invoice for (regular invoice).
        vals = super(SaleOrder, self.sudo())._prepare_invoice()
        vals.update({
            'carrier_id': self.carrier_id.id or False,
            'tracking_ref': self.customer_sales_order,
            'total_sales': self.total_est_sales,
            'total_landed_cost': self.total_est_landed_cost,
            'total_dcost': self.total_est_dcost,
            # 'analytic_account_id': self.analytic_account_id.id or False,
            'division_type_id': self.division_type_id.id or False,
            'total_so_weight': self.total_weight,
            'so_shipping_cost': self.pw_shipping_cost,
            'sales_manager_id': self.sales_manager_id.id or False,
        })
        return vals
