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


class MailMessage(models.Model):
    _inherit = "mail.message"

    @api.model
    def create(self, vals):
        user = False

        # if 'uid' in self._context:
        #     user = self.env['res.users'].browse(
        #         self._context.get('uid', 0))
        if self.env.user:
            user = self.env.user
        elif self.uid:
            user = self.env['res.users'].browse(
                self.env.context.get('uid', 0))

        ICPSudo = self.env['ir.config_parameter'].sudo()

        smtp_by_company = bool(ICPSudo.get_param(
            'smtp_by_user_and_company.smtp_by_company'))
        smtp_by_user = bool(ICPSudo.get_param(
            'smtp_by_user_and_company.smtp_by_user'))

        if user:
            active_company_id = self.env.company and self.env.company.id or 0

            if smtp_by_company and smtp_by_user:
                mail_server = self.env['ir.mail_server'].sudo().search(
                [('user_ids', 'in', [user.id]),('company_ids','in',[active_company_id])],limit=1)
                if mail_server:
                    vals.update({'mail_server_id': mail_server.id})
            elif smtp_by_company:
                mail_server = self.env['ir.mail_server'].sudo().search(
                    [('is_smtp_by_company', '=', True)])
                if mail_server:
                    out_mail_sever = self.env['ir.mail_server'].sudo().search([])
                    for mail_server in out_mail_sever:
                        for company in mail_server.company_ids:
                            if active_company_id == company.id:
                                vals.update({'mail_server_id': mail_server.id})
            else:
                out_mail_sever = self.env['ir.mail_server'].sudo().search(
                    [('user_ids', 'in', [user.id])],limit=1)
                if out_mail_sever:
                    vals.update({'mail_server_id': out_mail_sever.id})

        result = super(MailMessage, self).create(vals)
        return result