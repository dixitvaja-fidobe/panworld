# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.osv.expression import OR
from odoo.tools.safe_eval import safe_eval


class AccountMove(models.Model):
    _inherit = "account.move"

    search_multi_invoice = fields.Char(
        "Multiple search",
        compute="_compute_search_multi",
        search="_search_multi",
    )

    def _compute_search_multi(self):
        self.search_multi_invoice = False

    def _search_multi(self, operator, value):
        if operator == "=" or operator == "ilike":
            operator = "in"
            comparator = OR
        else:
            raise UserError(_("Operator %s is not usable with Multi Search", operator))

        value_list = value.split(" ") if " " in value else [value]

        search_account_move = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("custom_search_multi_value.search_account_move")
        )
        search_account_move = safe_eval(search_account_move)

        domain_list = []
        for search_field in search_account_move:
            domain_search_field = [(search_field, operator, tuple(value_list))]
            domain_list.append(domain_search_field)
        return comparator(domain_list)

