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

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def get_report_options_for_partner_ledger(self, options, user_email=None):
        partner_ledger_line = self.env['account.partner.ledger']
        company_ids = self.company_id.ids
        report_options = partner_ledger_line.with_context(allowed_company_ids=company_ids)._get_options(
            previous_options=options)
        partner_ledger_line._get_lines(report_options, line_id=None)
        pdf_data = partner_ledger_line.get_pdf(report_options)
        attachment = self.env['ir.attachment'].create({
            'name': "partner_ledger" + '_.pdf',
            'type': 'binary',
            'datas': base64.encodebytes(pdf_data),
            'res_model': None,  #'res.partner'
            'res_id': None,      #rec.id
            'mimetype': 'application/pdf'
        })

        xlsx_data = partner_ledger_line.get_xlsx(options)
        xlsx_attach = self.env['ir.attachment'].create({
            'name': 'partner_ledger' + '_.xls',
            'type': 'binary',
            'datas': base64.encodebytes(xlsx_data),
            'res_model': None,         #'res.partner',
            'res_id': None,              #rec.id,
            'mimetype': 'application/vnd.ms-excel'
        })

        domain = [('id', 'in', options['partner_ids'])] if options.get('partner_ids') else []
        for rec in self.search(domain):

            template_ctx = {
                'model_description': self.env['ir.model']._get('res.partner').display_name,
                'message': self.env['mail.message'].sudo().new(
                    dict(
                        body="<p>Dear %s,<br/>Here is your partner ledger report attached below. </p>" % rec.display_name,
                        record_name=_(rec.display_name))),
                'company': rec.company_id,
            }
            body = self.env['ir.qweb']._render('mail.mail_notification_light', template_ctx, minimal_qcontext=True,
                                               raise_if_not_found=False)
            body = self.env['mail.render.mixin']._replace_local_links(body)
            mail_vals = {
                'body_html': body,
                'subject': 'Partner Ledger %s' % rec.display_name,
                'author_id': self.env.user.partner_id.id,
                'email_from': user_email if user_email else self.env.user.additional_email or self.env.user.email_formatted,
                'email_to': rec.email,
                'attachment_ids': [(6, 0, [attachment.id, xlsx_attach.id])],
            }
            self.env['mail.mail'].sudo().create(mail_vals).send()