# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _


class AdvancePayment(models.TransientModel):
    _name = 'purchase.advance.payment'
    _description = 'Purchase Advance Payment'

    journal_id = fields.Many2one('account.journal', string="Payment Journal", required=True,
                                 domain=[('type', 'in', ['cash', 'bank'])])
    pay_amount = fields.Float(string="Payable Amount", required=True)
    date_planned = fields.Datetime(string="Advance Payment Date", index=True, default=fields.Datetime.now,
                                   required=True)

    @api.constrains('pay_amount')
    def check_amount(self):
        if self.pay_amount <= 0:
            raise ValidationError(_("Please Enter Postive Amount"))

    def make_payment(self):
        payment_obj = self.env['account.payment']
        purchase_ids = self.env.context.get('active_ids', [])
        purchase_id = self.env['purchase.order'].browse(purchase_ids)
        if purchase_ids:
            payment_res = self.get_payment(purchase_ids)
            payment_obj.create(payment_res)
            if purchase_id.account_payment_ids:
                new_purchase_obj = purchase_id.account_payment_ids.mapped('purchase_id')
                pending_advance_id = self.env['pending.advance.requests'].sudo().search([('purchase_id', '=', new_purchase_obj.id)])
                if pending_advance_id:
                    pending_advance_id.unlink()
            # payment = payment_obj.create(payment_res)
            # if payment and payment.move_id:
            #     purchase_order = self.env['purchase.order'].search([('invoice_ids', 'in', payment.move_id.id)], limit=1)
            #     try:
            #         activity_type_id = self.env.ref("mail.mail_activity_data_todo").id
            #     except ValueError:
            #         activity_type_id = False
                # for user in self.env.ref('bi_sale_purchase_advance_payment.manage_advance_payment').users:
                #     po = self.env['purchase.order'].sudo().browse(purchase_ids)
                #     activity = self.env["mail.activity"].sudo().create(
                #         {
                #             "activity_type_id": activity_type_id,
                #             "note": _(
                #                 "The Advanced Payment is Created now on purchase order %s with %s " % (
                #                     po.name, self.pay_amount)
                #             ),
                #             "user_id": user.id,
                #             "res_id": po.id,
                #             "res_model_id": self.env.ref(
                #                 "purchase.model_purchase_order"
                #             ).id,
                #         }
                #     )
            # payment.action_post()


        return {
            'type': 'ir.actions.act_window_close',
        }

    def get_payment(self, purchase_ids):
        purchase_obj = self.env['purchase.order']
        purchase_id = purchase_ids[0]
        purchase = purchase_obj.browse(purchase_id)
        payment_res = {
            'payment_type': 'outbound',
            'is_advanced_payment': True,
            'partner_id': purchase.partner_id.id,
            'partner_type': 'supplier',
            'journal_id': self[0].journal_id.id,
            'company_id': purchase.company_id,
            'currency_id': purchase.currency_id.id,
            'date': self[0].date_planned,
            'amount': self[0].pay_amount,
            'purchase_id': purchase.id,
            'po_value':purchase.amount_total,
            # 'name': "Advance Payment" + " - " + purchase.name,
            'payment_method_id': self.env.ref('account.account_payment_method_manual_out').id
        }
        return payment_res
