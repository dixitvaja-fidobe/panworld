# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import models, api
from odoo.exceptions import UserError

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def unlink(self):
        for attachment in self:
            if (attachment.res_model == 'stock.picking' and
                attachment.name == 'No Backorder-Partial Delivery Report.xlsx'):
                raise UserError("Security Warning!!!\nThis report cannot be deleted.")
        return super().unlink()