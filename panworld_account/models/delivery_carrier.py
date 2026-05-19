# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import models, fields, api, _


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    def _get_conversion_currencies(self, order, conversion):
        # Override method to pass values base on account move object.
        if order._name == 'account.move':
            if conversion == 'company_to_pricelist':
                from_currency, to_currency = order.company_id.currency_id, order.currency_id
            elif conversion == 'pricelist_to_company':
                from_currency, to_currency = order.currency_id, order.company_id.currency_id

            return from_currency, to_currency
        else:
            return super()._get_conversion_currencies(order, conversion)

    def _compute_currency(self, order, price, conversion):
        # Override method to pass values base on account move object.
        if order._name == 'account.move':
            from_currency, to_currency = self._get_conversion_currencies(order, conversion)
            if from_currency.id == to_currency.id:
                return price
            return from_currency._convert(price, to_currency, order.company_id, order.invoice_date or fields.Date.today())
        else:
            return super()._compute_currency(order, price, conversion)

    def _get_price_available(self, order):
        # Override method to pass values base on account move object.
        self.ensure_one()
        self = self.sudo()
        order = order.sudo()
        if order._name == 'account.move':
            total = weight = volume = quantity = 0
            total_delivery = 0.0
            for line in order.invoice_line_ids:
                if line.parent_state == 'cancel':
                    continue
                if not line.product_id:
                    continue
                if line.product_id.type == "service":
                    continue
                qty = line.product_uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
                weight += (line.product_id.weight or 0.0) * qty
                volume += (line.product_id.volume or 0.0) * qty
                quantity += qty
            total = (order.amount_total or 0.0) - total_delivery

            total = self._compute_currency(order, total, 'pricelist_to_company')

            return self._get_price_from_picking(total, weight, volume, quantity)
        else:
            return super()._get_price_available(order)

    def rate_shipment(self, order):
        # Override method to pass values base on account move object.
        self.ensure_one()
        if order._name == 'account.move':
            if hasattr(self, '%s_rate_shipment' % self.delivery_type):
                res = getattr(self, '%s_rate_shipment' % self.delivery_type)(order)
                # apply fiscal position
                company = self.company_id or order.company_id or self.env.company
                res['price'] = self.product_id._get_tax_included_unit_price(
                    company,
                    company.currency_id,
                    order.invoice_date,
                    'sale',
                    fiscal_position=order.fiscal_position_id,
                    product_price_unit=res['price'],
                    product_currency=company.currency_id
                )
                # apply margin on computed price
                res['price'] = float(res['price']) * (1.0 + (self.margin / 100.0))
                # save the real price in case a free_over rule overide it to 0
                res['carrier_price'] = res['price']
                return res
        else:
            return super().rate_shipment(order)