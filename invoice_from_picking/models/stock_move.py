# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import _, api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_moves_taxes(self, moves, inv_type):
        # extra moves with the same picking_id and product_id of a move have the same taxes
        extra_move_tax = {}
        is_extra_move = {}
        for move in moves:
            if move.picking_id:
                is_extra_move[move.id] = True
                if not (move.picking_id, move.product_id) in extra_move_tax:
                    extra_move_tax[move.picking_id, move.product_id] = 0
            else:
                is_extra_move[move.id] = False
        return (is_extra_move, extra_move_tax)

    def _get_master_data(self, move, company):
        """ returns a tuple (browse_record(res.partner), ID(res.users), ID(res.currency)"""
        currency = company.currency_id.id
        if move.picking_id.sale_id:
            partner = move.picking_id.sale_id.partner_id
        elif move.picking_id.purchase_id:
            partner = move.picking_id.purchase_id.partner_id
        else:
            partner = move.picking_id and move.picking_id.partner_id
        if partner:
            code = self.get_code_from_locs(move)
            if partner.property_product_pricelist and code == "outgoing":
                currency = partner.property_product_pricelist.currency_id.id
        return partner, self._uid, currency

    def get_code_from_locs(self, move, location_id=False, location_dest_id=False):
        code = "internal"
        src_loc = location_id or move.location_id
        dest_loc = location_dest_id or move.location_dest_id
        if src_loc.usage == "internal" and dest_loc.usage != "internal":
            code = "outgoing"
        if src_loc.usage != "internal" and dest_loc.usage == "internal":
            code = "incoming"
        return code

    def _get_taxes(self, move):
        if move.purchase_line_id.taxes_id:
            return [tax.id for tax in move.purchase_line_id.taxes_id]
        if move.sale_line_id.tax_id:
            return [tax.id for tax in move.sale_line_id.tax_id]
        return []

    def _get_price_unit_invoice(self, move_line, move_type):
        if move_type in ("in_invoice", "in_refund"):
            return move_line.price_unit
        else:
            price = move_line.sale_line_id.price_unit
            if price:
                return price

    def _get_invoice_line_vals(self, move, partner, inv_type):
        name = False
        move_lies = []
        # for move in moves:
        if inv_type in ("out_invoice"):
            account_id = move.product_id.property_account_income_id.id
            if not account_id:
                account_id = (
                    move.product_id.categ_id.property_account_income_categ_id.id
                )
            if move.sale_line_id:
                name = move.sale_line_id.name
        else:
            account_id = move.product_id.property_account_expense_id.id
            if not account_id:
                account_id = (
                    move.product_id.categ_id.property_account_expense_categ_id.id
                )

        # set UoS if it's a sale and the picking doesn't have one
        uos_id = move.product_uom.id
        quantity = move.quantity

        taxes_ids = self._get_taxes(move)
        if self._get_price_unit_invoice(move, inv_type) != None:
            price = self._get_price_unit_invoice(move, inv_type)
            subtotal = quantity * self._get_price_unit_invoice(move, inv_type)
        else:
            price = 0.0
            subtotal = quantity
        return {
            "name": name or move.name,
            "move_id": move.id,
            "account_id": account_id,
            "product_id": move.product_id.id,
            "quantity": quantity,
            "price_subtotal": subtotal,
            "price_unit": price,
            "tax_ids": [(6, 0, taxes_ids)],
            "discount": move.sale_line_id.discount,
            "analytic_account_id": move.sale_line_id.order_id.analytic_account_id.id
            or False,
            "product_uom_id": uos_id,
        }

    def _prepare_account_move_vals(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        # Overwrite method to pass date as scheduled date in journal entries.
        vals = super()._prepare_account_move_vals(credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost)
        if self.picking_id and self.picking_id.scheduled_date:
            vals.update({
                'date': self.picking_id.scheduled_date
            })
        return vals
