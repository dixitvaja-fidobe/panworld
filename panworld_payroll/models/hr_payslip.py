# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import api, fields, models
from dateutil.relativedelta import relativedelta
from odoo.tools.float_utils import float_round

class HrPayslipTus(models.Model):
    _inherit = 'hr.payslip'

    job_title = fields.Char(related='employee_id.job_title')

    payment_method = fields.Selection(
        string='Payment Method',
        selection=[('WPS', 'WPS'),
                   ('BANK', 'BANK'),
                   ('CASH', 'CASH'),
                   ('CHEQUE', 'CHEQUE'),
                   ],
        )

    def _compute_remaining_leaves(self):
        if self.employee_id:
            return float(self.employee_id.allocation_display) - float(self.employee_id.allocation_used_display)
    
    def action_print_payslip(self):
        action = self.env.ref('panworld_payroll.payslip_ext')
        datas = {
            'payslip_id': self.ids,
        }
        return action.report_action(self, data=datas)

    def get_pay_date(self):
        paydate = self.date_to + relativedelta(months=1)
        return paydate.strftime('%Y-%m-01')

    def get_salary_month(self):
        return self.date_to.strftime("%B")

    def _prepare_line_values(self, line, account_id, date, debit, credit):
        vals = super(HrPayslipTus, self)._prepare_line_values(line=line, account_id=account_id, date=date, debit=debit, credit=credit)
        if self.contract_id.analytic_tag_id:
            vals['analytic_tag_ids'] = [(6, 0, self.contract_id.analytic_tag_id.ids)]
        if not vals.get('partner_id'):
            if self.employee_id.related_partner_id:
                vals['partner_id'] = self.employee_id.related_partner_id.id
            elif self.employee_id.address_home_id:
                vals['partner_id'] = self.employee_id.address_home_id.id
        return vals
