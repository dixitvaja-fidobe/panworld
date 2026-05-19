import xlsxwriter
from odoo.exceptions import UserError
from odoo import models, fields, api, exceptions, _
import base64
import binascii
import logging
import os
import tempfile
import calendar
from datetime import date, timedelta

class PurchaseOrderTrackerWizard(models.TransientModel):
    _name = 'purchase.order.tracker.wizard'
    _description = 'Purchase Order trcaker Wizard'

    start_date = fields.Date(string='Start Date', default=fields.Date.today().replace(day=1), required=True)
    end_date = fields.Date(string='End Date', default=fields.Date.today().replace(day=calendar.monthrange(date.today().year, date.today().month)[1]), required=True)
    po_ids = fields.Many2many('purchase.order', string="Purchase Order")

    @api.onchange('start_date', 'end_date')
    def onchange_start_end_date(self):
        if self.start_date and self.end_date:
            po_list = self.env['purchase.order'].search(
                [('date_approve', '>=', self.start_date), ('date_approve', '<=', self.end_date), ('state', 'not in', ['cancel','draft'])]).ids
            return {'domain': {'po_ids': [('id', 'in', po_list)]}}


    def view_purchase_tracker_report(self):
        self.ensure_one()
        view = self.env.ref('panworld_purchase.purchase_tracker_view_tree')
        domain = []
        if self.start_date and self.end_date:
            domain = [('po_date', '<', self.end_date), ('po_date', '>', self.start_date)]
        if self.po_ids:
            domain += [('po_id', 'in', self.po_ids.ids)]

        view_id = view and view.id or False
        context = dict(self.env.context or {})

        return {
            'name': 'Purchase tracker',
            'view_mode': 'tree',
            'views': [(view_id, 'tree')],
            'res_model': 'purchase.tracker.report',
            'type': 'ir.actions.act_window',
            'domain': domain,
            'target': 'current',
            'context': context,
        }