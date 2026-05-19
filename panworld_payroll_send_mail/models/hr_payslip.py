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


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def action_open_payslip_employee_send_mail_wizard(self):
        # this button method in the hr.payslip tree view in server action ('Send By Email')
        view_id = self.env.ref('panworld_payroll_send_mail.panworld_payroll_send_mail').id
        selected_records = self.env.context.get('active_ids')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Send Mail Wizard',
            'res_model': 'payslips.employee',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'force_email': True, 'model_name': 'hr.payslip', 'active_ids': selected_records},
        }
