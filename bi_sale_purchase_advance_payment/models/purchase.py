# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
import datetime

from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    account_payment_ids = fields.One2many('account.payment', 'purchase_id', string="Pay purchase advanced")
    is_request_advance_payment = fields.Boolean(string='Freeze Advance Payment Request', copy=False)

    def send_mail_request_advance_payment(self):
        for rec in self:
            template_id = self.env.ref('bi_sale_purchase_advance_payment.request_advance_payment_mail_template')
            if template_id and not rec.is_request_advance_payment:
                email_values = template_id.generate_email(rec.id,
                                                          fields=['subject', 'body_html', 'email_from', 'partner_to'])

                subject = ('Advance Payment Request %s  %s ' % (rec.name, rec.partner_id.name))
                user = self.env['res.users'].search([]).filtered(
                    lambda x: x.has_group('bi_sale_purchase_advance_payment.advance_payments_creator'))
                email_values['subject'] = subject
                email_values['recipient_ids'] = [(6,0, user.partner_id.ids)]
                template_id.send_mail(rec.id, force_send=True, email_values=email_values or None)
                rec.is_request_advance_payment = True
            value = {'po_value':rec.amount_total, 'partner_id': rec.partner_id.id, 'purchase_id': rec.id, 'date': datetime.date.today(), 'company_id': rec.company_id.id, 'po_total':rec.po_total, 'currency_id': rec.currency_id.id}
            self.env['pending.advance.requests'].create(value)