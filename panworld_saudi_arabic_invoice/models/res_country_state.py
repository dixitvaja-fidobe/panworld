# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
import base64
from odoo import api, fields, models, _
from odoo.tools import float_repr
from odoo.exceptions import UserError



class CountryState(models.Model):
    _inherit = 'res.country.state'

    code = fields.Char(string='State Code', help='The state code.', required=True)