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
import base64



class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    def _get_reports_buttons(self, options):
        res = super()._get_reports_buttons(options)
        # res.append({'name': _('Send Mail'), 'sequence': 10, 'action': 'send_mail_notification'})
        res.append({'name': _('Send Mail'), 'sequence': 12, 'action': 'send_mail_wizard'})
        return res

    def send_mail_notification(self, options, user_email=None):
        self.env['res.partner'].get_report_options_for_partner_ledger(options, user_email)
        action = self.env["ir.actions.actions"]._for_xml_id("account_reports.action_account_report_partner_ledger")
        return action

    def send_mail_wizard(self, options):
        new_context = self.env.context.copy()
        new_context['my_context_option'] = options
        new_wizard = self.with_context(new_context).env['partner.ledger.wizard'].create(
            {'user_email': self.env.user.additional_email})
        view_id = self.env.ref('panworld_email_configuration.partner_ledger_send_mail_wizard').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Send Mail'),
            'view_mode': 'form',
            'res_model': 'partner.ledger.wizard',
            'target': 'new',
            'res_id': new_wizard.id,
            'views': [[view_id, 'form']],
            'context': new_context,
        }






