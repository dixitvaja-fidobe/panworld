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
from odoo.tools import float_compare
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_round
from odoo import Command, api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    move_line_ids = fields.Many2many(
        comodel_name="stock.move",
        relation="stock_move_invoice_line_rel",
        column1="invoice_line_id",
        column2="move_id",
        string="Related Stock Moves",
        readonly=True,
        copy=False,
        help="Related stock moves (only when the invoice has been"
        " generated from a sale order).",
    )

    def copy_data(self, default=None):
        """Copy the move_line_ids in case of refund invoice creating new invoices
        (refund_method="modify") for multiple records."""
        vals_list = super().copy_data(default)

        if self.env.context.get("force_copy_stock_moves"):
            for record, vals in zip(self, vals_list, strict=False):
                if "move_line_ids" not in vals and record.move_line_ids:
                    vals["move_line_ids"] = [Command.set(record.move_line_ids.ids)]

        return vals_list