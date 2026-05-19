# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import fields, models, api


class ir_mail_server(models.Model):
    _inherit = "ir.mail_server"

    user_ids = fields.Many2many('res.users', 'ir_mail_server_user_rel', 'mail_server_id', 'user_id',string="User")
    company_ids = fields.Many2many(
        'res.company', 'ir_mail_server_rel', 'mail_server_id', 'company_id',
        string="Company")
    is_smtp_by_company = fields.Boolean("Is SMTP by Company", default=False)
    is_smtp_by_user = fields.Boolean("Is SMTP by User", default=False)

    @api.model
    def default_get(self, fields):
        res = super(ir_mail_server, self).default_get(fields)
        res_config_company = self.env['res.config.settings'].search(
            [], order='id desc', limit=1)
        if res_config_company.smtp_by_company:
            res.update({'is_smtp_by_company': True})
        if res_config_company.smtp_by_user:
            res.update({'is_smtp_by_user': True})
        return res
