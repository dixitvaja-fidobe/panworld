# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import _, models
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def button_confirm(self):
        # attempt to change the state of this order to be included in \
        #  the computation for check_limit function
        # res =
        if not self.additional_po_service_ids and not self.is_all_service:
            raise ValidationError(_(
                'Please add shipping cost to confirm this order!'))
        context = self.env.context or {}
        message = _(
                    """You Cannot confirm Order! \n"""
                    """This will exceed allowed Credit Limit."""
                )
        if not self.partner_id.is_validation_exempt :
            res = super(PurchaseOrder, self).button_confirm()
            self.partner_id.check_limit(self)
            prev_state = self.state
            self.state = "purchase"
            if self.partner_id.check_limit(self):
                self.state = prev_state
                raise ValidationError(message)
            return res
        if not context.get('confirmation_done'):
            context.update({'default_name': message ,
                            'purchase_obj':self._name,
                            'purchase_id':self.id})
            return {
                'name': _('Warning'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'confirm.credit.limit',
                'views': [(False, 'form')],
                'view_id': False,
                'target': 'new',
                'context': context
            }
        if context.get('confirmation_done') and \
            self.partner_id.is_validation_exempt:
            return super(PurchaseOrder, self).button_confirm()


