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


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.constrains('scheduled_date')
    def _check_scheduled_date(self):
        # Set restrict on date entry base on date configuration in company
        for rec in self:
            if rec.scheduled_date and rec.scheduled_date.date() > fields.Date.today() + datetime.timedelta(
                    days=rec.company_id.upper_date_limit):
                if rec.picking_type_code != 'outgoing':
                    if rec.company_id.upper_date_limit == 0:
                        raise ValidationError(_('Material Received Date should be today date!'))
                    else:
                        raise ValidationError(_(
                            'Sorry, You are not allowed to create Material Received Date for %s days future!'
                        ) % rec.company_id.upper_date_limit)
                elif rec.picking_type_code == 'outgoing':
                    if rec.company_id.upper_date_limit == 0:
                        raise ValidationError(_('Order date should be today date!'))
                    else:
                        raise ValidationError(_(
                            'Sorry, You are not allowed to create Order for %s days future!'
                        ) % rec.company_id.upper_date_limit)
            elif rec.scheduled_date and rec.scheduled_date.date() < fields.Date.today() - datetime.timedelta(
                    days=rec.company_id.lower_date_limit):
                if rec.picking_type_code != 'outgoing':
                    if rec.company_id.lower_date_limit == 0:
                        raise ValidationError(_('Material Received Date should be today date!'))
                    else:
                        raise ValidationError(_(
                            "Sorry, You are not allowed to create Material Received Date for %s days back!"
                        ) % rec.company_id.lower_date_limit)
                elif rec.picking_type_code == 'outgoing':
                    if rec.company_id.lower_date_limit == 0:
                        raise ValidationError(_('Order date should be today date!'))
                    else:
                        raise ValidationError(_(
                            "Sorry, You are not allowed to create Order for %s days back!"
                        ) % rec.company_id.lower_date_limit)