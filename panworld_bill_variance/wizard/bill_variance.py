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


class BillVariance(models.TransientModel):
    _name = "bill.variance"
    _description = "Add Bill Variance Line"

    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True,
        help="Select an accounting account which will use for difference entries",
    )

    def button_confirm(self):
        for rec in self:
            ctx = dict(self.env.context) or {}
            if not rec.product_id.product_tmpl_id.property_account_expense_id:
                raise UserError(_("Please Configure Bill Variance Account in Product!"))
            if ctx.get("acount_move_active_model") == "account.move" and ctx.get(
                "acount_move_active_id"
            ):
                bill_rec = self.env["account.move"].browse(
                    ctx.get("acount_move_active_id")
                )
                for bill in bill_rec:
                    vals = {
                        "product_id": rec.product_id.id,
                        "account_id": rec.product_id.product_tmpl_id.property_account_expense_id.id,
                        "price_unit": bill.bill_difference_amount,
                    }
                    bill.update({"invoice_line_ids": [(0, 0, vals)]})
