# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import _, api, fields, models


class PendingAdvanceRequests(models.Model):
    _name = 'pending.advance.requests'
    _description = 'Pending Advance Requests'

    po_value = fields.Monetary('PO Value', currency_field="currency_id")
    po_total = fields.Float('PO Total')
    currency_id = fields.Many2one('res.currency', 'Currency')
    purchase_id = fields.Many2one('purchase.order','PO')
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    partner_id = fields.Many2one("res.partner", "Partner")
    date = fields.Date('Date')
