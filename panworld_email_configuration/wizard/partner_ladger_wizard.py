# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import fields, models, _, api


class PartnerLedgerWizard(models.TransientModel):
    _name = 'partner.ledger.wizard'
    _description = 'Partner Ledger wiz'
    _rec_name = 'user_email'

    user_email = fields.Selection(selection='_get_dynamic_email', string="From Email", required=True,
                                  default=lambda self: self.env.user.additional_email)

    def _get_dynamic_email(self):
        return [
            (self.env.user.additional_email, self.env.user.additional_email),
            (self.env.user.email_formatted, self.env.user.email_formatted),
        ]

    def send_mail_wiz(self):
        report_options = self.env.context['my_context_option']
        esc = self.env['account.report'].send_mail_notification(report_options, user_email=self.user_email)
        return esc
