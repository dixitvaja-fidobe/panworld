# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    # adding discount to depends
    @api.depends("discount")
    def _compute_amount(self):
        return super()._compute_amount()

    def _prepare_compute_all_values(self):
        vals = super()._prepare_compute_all_values()
        vals.update({"price_unit": self._get_discounted_price_unit()})
        return vals

    discount = fields.Float(string="Discount (%)", related="po_discount", digits="Discount")

    _discount_limit = models.Constraint(
        'CHECK (discount <= 100.0)',
        "Discount must be lower than 100%."
    )

    def _get_discounted_price_unit(self):
        """Inheritable method for getting the unit price after applying
        discount(s).

        :rtype: float
        :return: Unit price after discount(s).
        """
        self.ensure_one()
        if self.discount:
            return self.price_unit * (1 - self.discount / 100)
        return self.price_unit
    #
    # def _get_stock_move_price_unit(self):
    #     """Get correct price with discount replacing current price_unit
    #     value before calling super and restoring it later for assuring
    #     maximum inheritability.
    #
    #     HACK: This is needed while https://github.com/odoo/odoo/pull/29983
    #     is not merged.
    #     """
    #     price_unit = False
    #     price = self._get_discounted_price_unit()
    #     if price != self.price_unit:
    #         # Only change value if it's different
    #         price_unit = self.price_unit
    #         self.price_unit = price
    #     price = super()._get_stock_move_price_unit()
    #     if price_unit:
    #         self.price_unit = price_unit
    #     return price

    def _get_stock_move_price_unit(self):
        """Get correct price with discount replacing current price_unit
        value before calling super and restoring it later for assuring
        maximum inheritability.

        HACK: This is needed while https://github.com/odoo/odoo/pull/29983
        is not merged.
        """
        # Use 'skip_update_price_unit' context key to avoid infinite
        # recursion. Updating the price_unit field here triggers the
        # 'write' method of 'purchase.order.line' in stock_account
        # module which triggers this method again.
        if self.env.context.get("skip_update_price_unit"):
            return super()._get_stock_move_price_unit()
        price_unit = False
        price = self._get_discounted_price_unit()
        if price != self.price_unit:
            # Only change value if it's different
            price_unit = self.price_unit
            self.with_context(skip_update_price_unit=True).price_unit = price
        price = super()._get_stock_move_price_unit()
        if price_unit:
            self.with_context(skip_update_price_unit=True).price_unit = price_unit
        return price

    @api.onchange("product_qty", "product_uom_id")
    def onchange_product_id(self):
        """
        Check if a discount is defined into the supplier info and if so then
        apply it to the current purchase order line
        """
        res = super().onchange_product_id()
        if self.product_id:
            date = None
            if self.order_id.date_order:
                date = self.order_id.date_order.date()
            seller = self.product_id._select_seller(
                partner_id=self.partner_id,
                quantity=self.product_qty,
                date=date,
                uom_id=self.product_uom_id,
            )
            self._apply_value_from_seller(seller)
        return res

    @api.model
    def _apply_value_from_seller(self, seller):
        """Overload this function to prepare other data from seller,
        like in purchase_triple_discount module"""
        if not seller:
            return
        self.discount = seller.discount

    def _prepare_account_move_line(self, move=False):
        vals = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        vals["discount"] = self.discount
        vals["name"] = self.name
        vals["price_unit"] = self.list_price
        vals["list_price"] = self.price_unit
        return vals

    @api.model
    def _prepare_purchase_order_line(
        self, product_id, product_qty, product_uom_id, company_id, supplier, po
    ):
        """Apply the discount to the created purchase order"""
        res = super()._prepare_purchase_order_line(
            product_id, product_qty, product_uom_id, company_id, supplier, po
        )
        partner = supplier.name
        uom_po_qty = product_uom_id._compute_quantity(product_qty, product_id.uom_po_id)
        seller = product_id.with_company(company_id)._select_seller(
            partner_id=partner,
            quantity=uom_po_qty,
            date=po.date_order and po.date_order.date(),
            uom_id=product_id.uom_po_id,
        )
        res.update(self._prepare_purchase_order_line_from_seller(seller))
        return res

    @api.model
    def _prepare_purchase_order_line_from_seller(self, seller):
        """Overload this function to prepare other data from seller,
        like in purchase_triple_discount module"""
        if not seller:
            return {}
        return {"discount": seller.discount}
