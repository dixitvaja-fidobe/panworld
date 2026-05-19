# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import fields, models

class AccountJournal(models.Model):
    _inherit = "account.journal"

    out_of_scope = fields.Boolean(string="Out of Scope",
                                  help="Enable this for the journal to manage the out of scope invoices with with "
                                       "separate sequence")
    cogs_account_id = fields.Many2one('account.account', string="COGS Account",
                                      check_company=True,
                                      domain="[('account_type', 'in', ('expense', 'expense_direct_cost', 'expense_other'))]")