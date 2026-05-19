# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import fields, models, _, api
import base64

class AccountPaymentTus(models.Model):
    _inherit = "account.payment"

    purchase_id = fields.Many2one('purchase.order', string="Purchase", readonly=False)
    sale_id = fields.Many2one('sale.order', string="Sale", readonly=True)
    is_advanced_payment = fields.Boolean(string='Is Advanced Payment', copy=False, default=False)

    payment_utr_no = fields.Char(string="Payment UTR Ref")
    attachment_upload = fields.Binary(string="Attachment Upload")
    file_name = fields.Char('File Name')
    # status_custom = fields.Selection([('created', 'Created'),
    #                                  ('not_created', 'Not Created')], string='Status 1')
    po_value = fields.Monetary('PO Value', compute='_compute_purchase_amount', store=True)
    partner_ids = fields.Many2many('res.partner', string='Recipients')

    @api.depends('purchase_id.amount_total')
    def _compute_purchase_amount(self):
        for rec in self:
            if rec.purchase_id and rec.state == 'draft':
                rec.po_value = rec.purchase_id.amount_total
            else:
                po_value = rec.po_value if rec.po_value and rec.purchase_id else 0.0
                rec.po_value = po_value

    # def action_post(self):
    #     res = super().action_post()
    #     for rec in self:
    #         if self.state == 'posted':
    #             if rec.is_advanced_payment:
    #                 active_id = rec.purchase_id.id or False
    #                 move_id = self.env['account.move'].sudo().browse(active_id)
    #                 purchase_order = self.env['purchase.order'].browse([active_id])
    #
    #                 try:
    #                     activity_type_id = self.env.ref("mail.mail_activity_data_todo").id
    #                 except ValueError:
    #                     activity_type_id = False
                    # for user in self.env.ref('bi_sale_purchase_advance_payment.advance_payment_paid_status').users:
                    #     self.env["mail.activity"].sudo().create(
                    #         {
                    #             "activity_type_id": activity_type_id,
                    #             "note": _(
                    #                 "The Advanced Payment is paid now on purchase order %s with %s " % (
                    #                     purchase_order.name, self.amount)
                    #             ),
                    #             "user_id": user.id,
                    #             "res_id": purchase_order.id,
                    #             "res_model_id": self.env.ref(
                    #                 "purchase.model_purchase_order"
                    #             ).id,
                    #         }
                    #     )
        # return res

    def mark_as_sent(self):
        res = super().mark_as_sent()
        if self.is_advanced_payment:
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            base_url += '/web#id=%d&view_type=form&model=%s' % (self.purchase_id.id, self.purchase_id._name)
            new_context = self.env.context.copy()
            new_context.update({'base_url': base_url})
            self.env.context = new_context
            for rec in self:
                template_id = self.env.ref('bi_sale_purchase_advance_payment.process_advance_payment_mail_template')
                if template_id:
                    email_values = template_id.generate_email(rec.id,
                                                              fields=['subject', 'body_html', 'email_from', 'partner_to'])
                    if self.attachment_upload:
                        attachment = self.env['ir.attachment'].create({
                            'name': self.file_name,
                            'type': 'binary',
                            'datas': self.attachment_upload,
                            'res_model': self._name,
                            'res_id': rec.id,
                            'mimetype': 'application/pdf'
                        })
                        email_values['attachment_ids'] = [(4, attachment.id)]
                    # subject = ('Advance Payment Processed  %s  %s ' % (rec.name, rec.partner_id.name))
                    subject = ('Advance Payment Processed  %s' % (rec.partner_id.name))
                    user = self.env['res.users'].search([]).filtered(
                        lambda x: x.has_group('bi_sale_purchase_advance_payment.advance_payments_request'))
                    email_values['subject'] = subject
                    # email_values['email_to'] = rec.purchase_id.partner_id.email
                    all_partners = user.partner_id + self.partner_ids
                    email_values['recipient_ids'] = [(6, 0, all_partners.ids)]
                    template_id.send_mail(rec.id, force_send=True, email_values=email_values or None)
        return res

