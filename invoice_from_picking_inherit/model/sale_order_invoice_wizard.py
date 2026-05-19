# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    _description = "Sales Advance Payment Invoice"

    # def create_invoices(self):
    #     if self._context.get('active_model') == 'sale.order':
    #         picking = self.env[self._context['active_model']].browse(self._context['active_id']).picking_ids.filtered(lambda x: not x.invoice_ids and x.state == 'done' and x.picking_type_code == 'outgoing')
    #         if 'invoiced' in picking.mapped('invoice_state'):
    #             raise UserError(_("No invoice created or invoice is  alrady created !"))
    #
    #     res = super(SaleAdvancePaymentInv, self).create_invoices()
    #     return res
