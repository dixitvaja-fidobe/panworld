# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import fields, models, api


class ResUsers(models.Model):
    _inherit = "res.users"

    additional_email = fields.Char(string='Employee Group Email')
