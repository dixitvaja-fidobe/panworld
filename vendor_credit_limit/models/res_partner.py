# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from datetime import datetime

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    credit_limit = fields.Float(string="Credit Limit", tracking=True)

    def check_limit(self, purchase_id):
        partner_id = purchase_id.partner_id
        vendor_currency_id = partner_id.property_purchase_currency_id
        # Other orders for this partner
        order_ids = self.env["purchase.order"].search(
            [
                ("partner_id", "=", partner_id.id),
                ("state", "in", ["purchase", "done"]),
                ("invoice_status", "!=", "invoiced"),
            ]
        )
        # Open Bills (unpaid or partially paid Bills --
        # It is already included in partner.credit
        vendor_bill_ids = self.env["account.move"].search(
            [
                ("partner_id", "=", partner_id.id),
                ("state", "in", ["posted"]),
                ("payment_state", "in", ["not_paid", "partial"]),
                ("move_type", "in", ["in_invoice", "in_refund"]),
            ]
        )
        diff_currency_bills = vendor_bill_ids.filtered(
            lambda bill: bill.currency_id != vendor_currency_id
        )
        # Initialize variables
        existing_order_balance = 0.0
        existing_bill_balance = 0.0
        # Confirmed orders total amount
        for order in order_ids.filtered(lambda x: x.currency_id != vendor_currency_id):
            # Converted order total to company currency
            converted_amount_total = order.currency_id._convert(
                order.amount_total,
                vendor_currency_id,
                self.env.company,
                fields.Date.context_today(self),
            )
            existing_order_balance += converted_amount_total
        for order in order_ids.filtered(lambda x: x.currency_id == vendor_currency_id):
            existing_order_balance += order.amount_total
        # Bills that are open (also shows up as part of partner.
        # Credit, so must be deducted
        for bill in diff_currency_bills:
            if (
                fields.Datetime.to_string(
                    bill.invoice_date_due or bill.date_invoice or bill.create_date
                )
            ) > fields.Datetime.to_string(datetime.now()):
                continue
            else:
                # Converted bill amount to company currency
                converted_amount_residual = bill.currency_id._convert(
                    bill.amount_residual,
                    vendor_currency_id,
                    bill.company_id,
                    fields.Date.context_today(self),
                )
                existing_bill_balance += converted_amount_residual
        for bill in vendor_bill_ids.filtered(
            lambda bill: bill.currency_id == vendor_currency_id
        ):
            if (
                fields.Datetime.to_string(
                    bill.invoice_date_due or bill.date_invoice or bill.create_date
                )
            ) > fields.Datetime.to_string(datetime.now()):
                continue
            else:
                existing_bill_balance += bill.amount_residual
        # All open Purchase orders + partner credit (AR balance) -
        # Open Bills (already included in partner credit)
        if (
            partner_id.credit_limit
            and (existing_bill_balance + existing_order_balance)
            > partner_id.credit_limit
        ):
            return True
        return False
