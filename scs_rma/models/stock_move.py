# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################

from odoo import _, fields, models, api
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = "stock.move"

    rma_id = fields.Many2one("rma.ret.mer.auth", string="RMA")