# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import _, api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    shipping_bill = fields.Boolean("Shipping Bill")