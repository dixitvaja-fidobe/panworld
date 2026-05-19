# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################

from odoo import models, fields, _, api


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'


    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    selection_mail = fields.Selection(
        selection='_list_of_email', string="From", default=lambda self: self.env.user.additional_email)

    def _list_of_email(self):
        return [
            (self.env.user.additional_email, self.env.user.additional_email),
            (self.env.user.email_formatted, self.env.user.email_formatted),
        ]

    @api.onchange('selection_mail')
    def _onchange_from_email_methods(self):
        if self.selection_mail:
            self.email_from = self.selection_mail

