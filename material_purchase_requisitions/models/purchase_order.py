# -*- coding: utf-8 -*-

from odoo import models, fields, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    custom_requisition_id = fields.Many2one(
        'material.purchase.requisition',
        string='Requisitions',
        copy=False
    )
    approver = fields.Char(
        string='Approved By',
        readonly=True,
        copy=False
    )
    approver_date = fields.Datetime(
        string='Approved Time',
        readonly=True,
        copy=False
    )

    def button_approve(self, force=False):
        result = super().button_approve(force=force)
        # write in batch; same approver for all records in self
        self.write({
            'approver': self.env.user.name,
            'approver_date': fields.Datetime.now(),  # or fields.Date.today() if your field is Date
        })
        return result

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()

        # Get the approver group and its users
        approver_group = self.env.ref('purchase.group_purchase_manager')
        approver_users = approver_group.sudo().user_ids

        # Use message_notify for better integration
        # for user in approver_users:
        #     self.with_context(mail_notify_author=True).message_notify(
        #         partner_ids=user.partner_id.ids,
        #         body=_(
        #             "Purchase Order %s has been confirmed and requires your approval.") % self.name,
        #         subject=_("Purchase Order Approval Required - %s") % self.name,
        #         subtype_xmlid='mail.mt_note',
        #     )
        #     self.env['bus.bus']._sendone(user.partner_id, 'simple_notification',
        #                                  {
        #                                      'type': 'warning',
        #                                      'message': _(
        #                                          "Purchase Order %s has been confirmed and requires your approval.") % self.name,
        #                                  })

        return res

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    custom_requisition_line_id = fields.Many2one(
        'material.purchase.requisition.line',
        string='Requisitions Line',
        copy=False
    )
