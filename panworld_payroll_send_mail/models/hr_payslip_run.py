# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import api, fields, models, _


class HRPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def action_open_payslip_employee_send_mail_wizard(self):
        # this button method in the hr.payslip.run form view Button name ('Send By Email')
        view_id = self.env.ref('panworld_payroll_send_mail.panworld_payroll_send_mail').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Send Mail Wizard',
            'res_model': 'payslips.employee',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'force_email': True},
        }
