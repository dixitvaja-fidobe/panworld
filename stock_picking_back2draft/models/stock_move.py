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
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = "stock.move"

    def action_back_to_draft(self):
        if self.filtered(lambda m: m.state != "cancel"):
            raise UserError(_("You can set back to draft only canceled moves"))
        self.write({"state": "draft"})
