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


class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    # @api.depends('is_paid', 'number_of_hours', 'payslip_id', 'contract_id.wage', 'payslip_id.sum_worked_hours')
    # def _compute_amount(self):
    #     for worked_days in self.filtered(lambda wd: not wd.payslip_id.edited):
    #         start_date = worked_days.payslip_id.date_from
    #         end_date = worked_days.payslip_id.date_to
    #         working_day = (end_date - start_date).days + 1
    #         if not worked_days.contract_id or worked_days.code == 'OUT':
    #             worked_days.amount = 0
    #             continue
    #         if worked_days.payslip_id.wage_type == "hourly":
    #             worked_days.amount = round((worked_days.payslip_id.contract_id.hourly_wage + worked_days.payslip_id.contract_id.l10n_ae_housing_allowance + worked_days.payslip_id.contract_id.l10n_ae_other_allowances) * worked_days.number_of_hours) if worked_days.is_paid else 0
    #         elif worked_days.code == 'LEAVE90':
    #             worked_days.amount = round(((worked_days.payslip_id.contract_id.contract_wage + worked_days.payslip_id.contract_id.house_rent_allowance_metro_nonmetro + worked_days.payslip_id.contract_id.supplementary_allowance) / working_day)) * worked_days.number_of_days if worked_days.is_paid else 0
    #         else:
    #             worked_days.amount = round(((worked_days.payslip_id.contract_id.contract_wage + worked_days.payslip_id.contract_id.l10n_ae_housing_allowance + worked_days.payslip_id.contract_id.l10n_ae_other_allowances) / working_day)) * worked_days.number_of_days if worked_days.is_paid else 0
                # worked_days.amount = (worked_days.payslip_id.contract_id.contract_wage + worked_days.payslip_id.contract_id.l10n_ae_housing_allowance + worked_days.payslip_id.contract_id.l10n_ae_housing_allowance) * worked_days.number_of_hours / (worked_days.payslip_id.sum_worked_hours or 1) if worked_days.is_paid else 0

