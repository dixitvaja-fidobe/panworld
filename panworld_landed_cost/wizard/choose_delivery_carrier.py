# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from multiprocessing import context
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def fixed_rate_shipment(self, order):
        carrier = self._match_address(order.partner_id)
        if not carrier:
            return {
                "success": False,
                "price": 0.0,
                "error_message": _(
                    "Error: this delivery method is not available for this address."
                ),
                "warning_message": False,
            }
        if order._name != "purchase.order":
            price = order.pricelist_id._get_product_price(
                self.product_id, 1.0
            )
        else:
            price = self.fixed_price
        return {
            "success": True,
            "price": price,
            "error_message": False,
            "warning_message": False,
        }

    def _compute_currency(self, order, price, conversion):
        from_currency, to_currency = self._get_conversion_currencies(order, conversion)
        if from_currency.id == to_currency.id:
            return price
        # Set the appropriate date field based on the order type
        if order._name == 'account.move':
            date = order.invoice_date or fields.Date.today()
        else:
            date = order.date_order or fields.Date.today()

        return from_currency._convert(
            price,
            to_currency,
            order.company_id,
            date,
        )

    def base_on_rule_rate_shipment(self, order):
        carrier = self._match_address(order.partner_id)
        if not carrier:
            return {
                "success": False,
                "price": 0.0,
                "error_message": _(
                    "Error: this delivery method is not available for this address."
                ),
                "warning_message": False,
            }

        try:
            price_unit = self._get_price_available(order)
        except UserError as e:
            return {
                "success": False,
                "price": 0.0,
                "error_message": e.args[0],
                "warning_message": False,
            }
        if order._name != "purchase.order":
            price_unit = self._compute_currency(
                order, price_unit, "company_to_pricelist"
            )
        else:
            price_unit = price_unit

        return {
            "success": True,
            "price": price_unit,
            "error_message": False,
            "warning_message": False,
        }



