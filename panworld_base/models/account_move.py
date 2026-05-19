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

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.constrains('invoice_date')
    def _check_invoice_date(self):
        # Set restrict on date entry base on date configuration in company
        for rec in self:
            if rec.invoice_date and rec.invoice_date > fields.Date.today() + datetime.timedelta(
                    days=rec.company_id.upper_date_limit):
                if rec.company_id.upper_date_limit == 0:
                    raise ValidationError(_('Invoice/Bill date should be today date!'))
                else:
                    raise ValidationError(_(
                        'Sorry, You are not allowed to create Invoice/Bill for %s days future!'
                    ) % rec.company_id.upper_date_limit)
            elif rec.invoice_date and rec.invoice_date < fields.Date.today() - datetime.timedelta(
                    days=rec.company_id.lower_date_limit):
                if rec.company_id.lower_date_limit == 0:
                    raise ValidationError(_('Invoice/Bill date should be today date!'))
                else:
                    raise ValidationError(_(
                        "Sorry, You are not allowed to create Invoice/Bill for %s days back!"
                    ) % rec.company_id.lower_date_limit)