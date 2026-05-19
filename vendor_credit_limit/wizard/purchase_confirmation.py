# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import fields, models, _


class ConfirmCreditLimit(models.TransientModel):
    _name = 'confirm.credit.limit'
    _description = "Confirm Credit Limit"

    name = fields.Text("Warning")

    def action_done_with_warnig(self):
        """
            Method will continue the Purchase order work flow after confirming
            the Purchase order.
            It will not break the flow.
        """
        context = dict(self.env.context) or {}
        model = context.get('purchase_obj')
        purchase_id = context.get('purchase_id')
        if model == 'purchase.order' and purchase_id:
            if  context.get('default_name'):
                del context['default_name']
            purchase_rec = self.env[model].browse(purchase_id)
            context.update({'confirmation_done':True})
            purchase_rec.with_context(context).button_confirm()
        return True
