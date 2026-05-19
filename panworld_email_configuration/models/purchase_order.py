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


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_rfq_send(self):
        attch_obj = self.env['ir.attachment']
        domain = [('res_id', '=', self.id), ('res_model', '=', 'purchase.order')]

        if self.state in ['purchase', 'done']:
            action = self.action_export_xls(mail_attach=True)
            domain += [('description', '=', 'PO')]

        else:
            action = self.action_rfq_export_xls(mail_attach=True)
            domain += [('description', '=', 'RFQ')]
        res = super(PurchaseOrder, self).action_rfq_send()


        attachment_id = attch_obj.search(domain)


        if not attachment_id:
            if self.state in ['purchase', 'done']:
                data = self.env.ref('purchase.action_report_purchase_order').sudo()._render_qweb_pdf(self.id)
            else:
                data = self.env.ref('purchase.report_purchase_quotation').sudo()._render_qweb_pdf(self.id)
            attachment_id = attch_obj.sudo().create({
                'name':  'Purchase Order' if self.state in ['purchase', 'done'] else 'Purchase Quotation',
                'datas': base64.b64encode(data[0]),
                'res_model': 'purchase.order',
                'res_id': self.id,
                'description': 'PO' if self.state in ['purchase', 'done'] else 'RFQ',
            })
        attach_id = attch_obj.sudo().search([('id', 'in', [attachment_id.id, action.id])])
        # if action:
        #     attach_id += attch_obj.sudo().search([('id', 'in', [attachment_id.id, action.id])])
        if res['context']:
            res['context']['default_attachment_ids'] = [(6, 0, attach_id.ids)]
        return res



