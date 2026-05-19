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


class Partner(models.Model):
    _inherit = "res.partner"

    name = fields.Char(string="Name", index=True, translate=True)
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street2")
    city = fields.Char(string="City")
    crn_number = fields.Char(string='CRN Number')
    address_arabic = fields.Char(string='Address in Arabic', translate=True)
    add_line_1_ar = fields.Char(translate=True)
    add_line_2_ar = fields.Char(translate=True)
    add_line_3_ar = fields.Char(translate=True)
    add_line_4_ar = fields.Char(translate=True)
    payment_term_condition = fields.Html(string='Terms & Conditions', translate=True)
    payment_term_condition_ar = fields.Html(string='Terms & Conditions (Arabic)', translate=True)
    summary = fields.Html(string='Summary', translate=True)
    summary_ar = fields.Html(string='Summary (Arabic)', translate=True)

