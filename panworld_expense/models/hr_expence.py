# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from ctypes import resize
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrExpense(models.Model):
    _inherit = "hr.expense"

    reference = fields.Char(string="Bill Reference")
    expense_partner_id = fields.Many2one("res.partner", "Partner")
    division_type_id = fields.Many2one('division.type',string="Division Type")
    bill_date = fields.Date(string='Bill Date')
    department_id = fields.Many2one(related='employee_id.department_id', string='Department')
    exchange_rate = fields.Float("Exchange Rate")
    total_amount_company = fields.Float(string="Total Amount")
