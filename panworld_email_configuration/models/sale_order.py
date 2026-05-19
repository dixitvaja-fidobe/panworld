# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_quotation_send(self):
        attch_obj = self.env['ir.attachment']

        res = super(SaleOrder, self).action_quotation_send()
        action = self.action_export_xls(mail_attach=True)
        attachment_id = attch_obj.search([('res_id', '=', self.id),
                                      ('res_model', '=', 'sale.order'),
                                      ('description', '=', 'Quotation')])



        if not attachment_id:
            data = self.env.ref('sale.action_report_saleorder').sudo()._render_qweb_pdf(self.id)
            attachment_id = attch_obj.sudo().create({
                'name':  'Sale Quotation',
                'datas': base64.b64encode(data[0]),
                'res_model': 'sale.order',
                'res_id': self.id,
                'description': 'Quotation',
            })
        if len(attachment_id) > 1:
            attach_id = attch_obj.sudo().search([('id', 'in', [attachment_id[0].id, action.id])])
        else:
            attach_id = attch_obj.sudo().search([('id', 'in', [attachment_id.id, action.id])])
        # if action:
        #     attach_id += attch_obj.sudo().search([('id', 'in', [attachment_id.id, action.id])])
        if res['context']:
            res['context']['default_attachment_ids'] = [(6, 0, attach_id.ids)]
        return res




