# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
import datetime
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # override from invoice_from_picking
    def _invoice_create_line(self, moves, journal_id, inv_type="out_invoice"):
        ''' To add picking ids on invoice override this method to attach picking in during create invoice from delivery'''
        invoice_obj = self.env["account.move"]
        move_obj = self.env["stock.move"]
        invoices = {}
        is_extra_move, extra_move_tax = move_obj._get_moves_taxes(moves, inv_type)
        product_price_unit = {}

        # Mapping to track pickings per invoice
        invoice_picking_ids = {} # key -> set of picking ids

        # Group moves by (partner/currency/company/user) and then by (SO/PO line)
        # This allows us to combine kit components into a single parent kit line.
        grouped_moves = {}
        for move in moves:
            company = move.company_id
            partner, user_id, currency_id = move_obj._get_master_data(move, company)

            key = (partner, currency_id, company.id, user_id)
            invoice_vals = self._get_invoice_vals(key, inv_type, journal_id, move)

            if key not in invoices:
                # Get account and payment terms
                invoice_id = self._create_invoice_from_picking(
                    move.picking_id, invoice_vals
                )
                invoice_id.picking_ids = [(4, move.picking_id.id)]
                invoices[key] = invoice_id.id
            else:
                invoice_id = invoice_obj.browse(invoices[key])
                invoice_id.picking_ids = [(4, move.picking_id.id)]
                merge_vals = {}
                if not invoice_id.ref or invoice_vals["ref"] not in invoice_id.ref.split(", "):
                    invoice_origin = filter(None, [invoice_id.ref, invoice_vals["ref"]])
                    merge_vals["ref"] = ", ".join(invoice_origin)
                if invoice_vals.get("name", False) and (not invoice_id.name or invoice_vals["name"] not in invoice_id.name.split(", ")):
                    invoice_name = filter(None, [invoice_id.name, invoice_vals["name"]])
                    merge_vals["name"] = ", ".join(invoice_name)
                if merge_vals:
                    invoice_id.write(merge_vals)

            invoice_line_vals = move_obj._get_invoice_line_vals(move, partner, inv_type)
            invoice_line_vals["move_id"] = invoices[key]
            invoice_line_vals["ref"] = origin
            invoice_line_vals["sale_line_ids"] = move.sale_line_id
            invoice_line_vals["purchase_line_id"] = move.purchase_line_id

            if not is_extra_move[move.id]:
                product_price_unit[invoice_line_vals["product_id"]] = invoice_line_vals[
                    "price_unit"
                ]
            if (
                    is_extra_move[move.id]
                    and (invoice_line_vals["product_id"]) in product_price_unit
            ):
                invoice_line_vals["price_unit"] = product_price_unit[
                    invoice_line_vals["product_id"]
                ]
            if is_extra_move[move.id]:
                desc = (
                               inv_type in ("out_invoice")
                               and move.product_id.product_tmpl_id.description_sale
                       ) or (
                               inv_type in ("purchase")
                               and move.product_id.product_tmpl_id.description_purchase
                       )
                invoice_line_vals["name"] += " " + desc if desc else ""
                if extra_move_tax[move.picking_id, move.product_id]:
                    invoice_line_vals["invoice_line_tax_id"] = extra_move_tax[
                        move.picking_id, move.product_id
                    ]
                # the default product taxes
                elif (0, move.product_id) in extra_move_tax:
                    invoice_line_vals["invoice_line_tax_id"] = extra_move_tax[
                        0, move.product_id
                    ]
            invice_line = invoice_id.update(
                {"invoice_line_ids": [(0, None, invoice_line_vals)]}
            )
            move_data = self.env["account.move"].browse(invoices[key])

            move.picking_id.write({"invoice_state": "invoiced"})
            if invoice_id and move.picking_id.sale_id:
                invoice_id.pw_shipping_cost = move.picking_id.sale_id.pw_shipping_cost

        for mv in moves:
            if mv.picking_id:
                invoice_id.write({"picking_ids": [(6, 0, mv.picking_id.ids)]})

        for inv_line in invoice_id.invoice_line_ids:
            for move in moves:
                if move.sale_line_id and move.sale_line_id.id in inv_line.sale_line_ids.ids:
                    # if inv_line.sale_line_ids.id == move.sale_line_id.id:
                    #     if move.sale_line_id:
                    move.sale_line_id.invoice_lines = [(4, inv_line.id)]

                if move.purchase_line_id:
                    if inv_line.purchase_line_id.id == move.purchase_line_id.id:
                        move.purchase_line_id.invoice_lines = [(4, inv_line.id)]

        if invoice_id:
            invoice_id._compute_amount()

        return invoices.values()
