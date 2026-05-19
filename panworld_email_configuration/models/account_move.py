# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64

class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    # def action_invoice_sent(self):
    #     attch_obj = self.env['ir.attachment']
    #
    #     res = super(AccountMoveInherit, self).action_invoice_sent()
    #     attachment_id = attch_obj.search([('res_id', '=', self.id),
    #                                       ('res_model', '=', 'account.move'),
    #                                       ('description', 'in', ['Invoice', 'saudi', 'maarif'])])
    #     d_list = attachment_id.ids if attachment_id else []
    #     if len(attachment_id) < 3:
    #         # Render regular invoice PDF
    #         invoice_pdf = self.env.ref('account.account_invoices').sudo()._render_qweb_pdf(self.id)
    #
    #         # Render Saudi Arabia invoice PDF
    #         saudi_invoice_pdf = self.env.ref(
    #             'panworld_saudi_arabic_invoice.action_report_panworld_saudi_arabic').sudo()._render_qweb_pdf(self.id)
    #
    #         # Render Saudi Arabia - Maarif invoice PDF
    #         saudi_invoice_Maarif_pdf = self.env.ref(
    #             'panworld_saudi_arabic_invoice.action_report_panworld_saudi_arabic_maarif').sudo()._render_qweb_pdf(self.id)
    #
    #         # Create attachments
    #         # data_templ = [
    #         #     {'name': 'Invoice', 'datas': base64.b64encode(invoice_pdf[0]), 'description': 'Invoice'},
    #         #     {'name': 'Saudi Arabia - Invoice', 'datas': base64.b64encode(saudi_invoice_pdf[0]),
    #         #      'description': 'Saudi Arabia - Invoice'}
    #         # ]
    #         data_templ =[invoice_pdf, saudi_invoice_pdf, saudi_invoice_Maarif_pdf]
    #
    #         d_list = []
    #         for rec in data_templ:
    #             attachment = attch_obj.sudo().create({
    #                 'name': 'Invoice',
    #                 'datas': base64.b64encode(rec[0]),
    #                 'res_model': 'account.move',
    #                 'res_id': self.id,
    #
    #             })
    #             if rec == data_templ[0]:
    #                 attachment['name'] = 'Invoice'
    #                 attachment['description'] = 'Invoice'
    #             elif rec == data_templ[1]:
    #                 attachment['name'] = 'Saudi Arabia_%s' % (self.name)
    #                 attachment['description'] = 'saudi'
    #             else:
    #                 attachment['name'] = 'Saudi Arabia_maarif_%s' % (self.name)
    #                 attachment['description'] = 'maarif'
    #             d_list.append(attachment.id)
    #
    #     # Assuming that you want to use the last created attachment
    #     attach_id = attch_obj.sudo().search([('id', 'in', d_list)])
    #     if res['context']:
    #         res['context']['default_attachment_ids'] = [(6, 0, attach_id.ids)]
    #     return res