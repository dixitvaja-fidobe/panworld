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


class PayslipsEmployee(models.TransientModel):
    _name = 'payslips.employee'
    _description = 'Payslips Employee'

    user_email = fields.Selection(selection='_get_dynamic_email', string="From Email", default=lambda self: self.env.user.additional_email)

    def _get_dynamic_email(self):
        if self.env.user.login and self.env.user.additional_email:
            return [("normal_email", self.env.user.login), ("additional_email", self.env.user.additional_email)]
        else:
            return [("normal_email", self.env.user.login)]

    def send_mail_employee(self):
        if self.env.context.get('active_model') == 'hr.payslip.run':
            active_id = self.env['hr.payslip.run'].browse(self.env.context.get('active_id', False))
            template_id = self.env.ref('panworld_payroll_send_mail.email_template_send_hr_payslip_payroll')
            if active_id.slip_ids:
                for payslip in active_id.slip_ids:
                    if self.user_email == 'additional_email':
                        template_id.email_from = self.env.user.additional_email
                    else:
                        template_id.email_from = self.env.user.login
                    template_id.send_mail(res_id=payslip.id, force_send=True, raise_exception=False, email_values=None)

        if self.env.context.get('model_name') == 'hr.payslip' and self.env.context.get('active_ids'):
            active_ids = self.env['hr.payslip'].browse(self.env.context.get('active_ids'))
            template_id = self.env.ref('panworld_payroll_send_mail.email_template_send_hr_payslip_payroll')
            if active_ids:
                for payslip in active_ids:
                    if self.user_email == 'additional_email':
                        template_id.email_from = self.env.user.additional_email
                    else:
                        template_id.email_from = self.env.user.login
                    template_id.send_mail(res_id=payslip.id, force_send=True, raise_exception=False, email_values=None)

