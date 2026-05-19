# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_back_to_draft(self):
        self.move_ids.action_back_to_draft()
