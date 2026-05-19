# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import api, fields, models, _


class StockMove(models.Model):
    _inherit = "stock.move"


    # def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description):
    #     # This method returns a dictionary to provide an easy extension hook to modify the valuation lines (see purchase for an example)
    #
    #     # Method inherited for only sale order out going move as per client requirement
    #     self.ensure_one()
    #     rslt = super()._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description)
    #     if self.picking_id and not self.picking_id.rma_id and self.picking_id.analytic_account_id and \
    #         self.picking_id.picking_type_id.code =='outgoing':
    #         credit_line_vals = rslt.get('credit_line_vals')
    #         debit_line_vals = rslt.get('debit_line_vals')
    #         credit_line_vals.update({'analytic_account_id':self.picking_id.analytic_account_id.id})
    #         debit_line_vals.update({'analytic_account_id':self.picking_id.analytic_account_id.id})
    #         if rslt.get('price_diff_line_vals'):
    #             price_diff_line_vals = rslt.get('debit_line_vals')
    #             price_diff_line_vals.update({'analytic_account_id':self.picking_id.analytic_account_id.id})
    #             rslt.update({'price_diff_line_vals': price_diff_line_vals})
    #         rslt.update({'credit_line_vals': credit_line_vals, 'debit_line_vals': debit_line_vals})
    #     return rslt
