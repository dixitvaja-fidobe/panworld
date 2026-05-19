# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = "account.move"

    rma_id = fields.Many2one("rma.ret.mer.auth", string="RMA", tracking=True)

    def action_post(self):
        # Set validation if return GRN are not done.
        for rec in self:
            if rec.rma_id and rec.rma_id.rma_type in ['customer', 'sale_direct']:
                if any(pick.state != "done" for pick in rec.rma_id.stock_picking_ids):
                    raise ValidationError(
                        _("To confirm this invoice, first process the Return GRN!")
                    )
        return super().action_post()