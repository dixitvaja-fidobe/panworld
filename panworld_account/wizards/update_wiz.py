# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import fields,models, _

class UpdateWiz(models.TransientModel):
    _name = "update.wiz"

    sales_manager_id = fields.Many2one("hr.employee", string="Sales Manager")
    partner_id = fields.Many2one("res.partner", string="Partner")
    date = fields.Date("Date")

    def update_sale_manager(self):
        """Update the Sale manager field as bulk for the selected invoices"""
        active_ids = self.env.context.get('active_ids')
        invoices = self.env['account.move'].browse(active_ids)
        for invoice in invoices:
            invoice.write({'sales_manager_id': self.sales_manager_id.id})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'SUCCESS',
                'message': _('%s Invoice(s) updated with new Sales managers successfully', len(invoices)),
                'type': 'success',
                'sticky': False,
            }
        }
    def update_partner_and_date(self):
        """Update the Partner and(or) Date fields as bulk for the selected invoices"""
        active_ids = self.env.context.get('active_ids')
        invoices = self.env['account.move'].browse(active_ids)
        for invoice in invoices:
            vals = {}
            if self.partner_id:
                vals['partner_id'] = self.partner_id.id
            if self.date:
                vals['invoice_date'] = self.date
            if vals:
                invoice.write(vals)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'SUCCESS',
                'message': _('%s Invoice(s) updated successfully', len(invoices)),
                'type': 'success',
                'sticky': False,
            }
        }
