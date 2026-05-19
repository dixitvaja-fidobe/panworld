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
from odoo.exceptions import ValidationError
import datetime


class ResCompany(models.Model):
    _inherit = 'res.company'

    upper_date_limit = fields.Integer(
        string='Upper Date Limit',
        help='Set restrict on future date for RFQ, PO, SO, GRN, Inv and Bills etc')
    lower_date_limit = fields.Integer(
        string='Lower Date Limit', default=59,
        help='Set restrict on past date for RFQ, PO, SO, GRN, Inv and Bills etc')


