# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import models, api


class Mail(models.Model):
    _inherit = "mail.mail"

    @api.model
    def create(self, vals):

        user = False

        if 'uid' in self.env.context:
            user = self.env['res.users'].browse(
                self.env.context.get('uid', 0))
        elif self.env.user:
            user = self.env.user
        elif self.uid:
            user = self.env['res.users'].browse(
                self.env.context.get('uid', 0))

        ICPSudo = self.env['ir.config_parameter'].sudo()

        smtp_by_company = bool(ICPSudo.get_param(
            'smtp_by_user_and_company.smtp_by_company'))
        smtp_by_user = bool(ICPSudo.get_param(
            'smtp_by_user_and_company.smtp_by_user'))

        active_company_id = self.env.company and self.env.company.id or 0
        
        if smtp_by_company and smtp_by_user and user:
            out_mail_sever = self.env['ir.mail_server'].search(
                [('company_ids', '=', active_company_id),('user_ids', 'in', [user.id])], limit=1)
        elif smtp_by_company and active_company_id:
            out_mail_sever = self.env['ir.mail_server'].search(
                [('company_ids', '=', active_company_id)], limit=1)
        elif smtp_by_user and user:
            out_mail_sever = self.env['ir.mail_server'].search(
                [('user_ids', 'in', [user.id])], limit=1)
        else:
            return super(Mail, self).create(vals)

        if out_mail_sever:
            active_u_name = user.partner_id and user.partner_id.name or ''
            active_u_email = user.partner_id and user.partner_id.email or ''
            active_u_user = out_mail_sever.smtp_user or ''

            if active_u_user != '':
                email_from = active_u_name + " " + "<" + active_u_user + ">"
                reply_to = active_u_name + " " + "<" + \
                    active_u_email or active_u_user
                vals.update({
                    'email_from': email_from, 'reply_to': reply_to
                })
            vals.update({'mail_server_id': out_mail_sever.id})

        result = super(Mail, self).create(vals)
        return result


