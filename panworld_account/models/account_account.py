# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#
##############################################################################
from odoo import fields, models

class AccountAccount(models.Model):
    """Add Expense Account for the counter line for the Deferred expense"""
    _inherit = "account.account"

    deferred_account_id = fields.Many2one("account.account", string="Deferred A/C for Expense", copy=False)
