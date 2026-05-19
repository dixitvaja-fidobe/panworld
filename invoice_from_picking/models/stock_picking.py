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


class StockPicking(models.Model):
    _inherit = "stock.picking"

    invoice_state = fields.Selection(
        [("invoiced", "Invoiced"), ("2binvoiced", "To Be Invoiced")],
        default="2binvoiced",
        string="Invoice Control",
    )
    invoice_id = fields.Many2one("account.move")

    def _get_partner_to_invoice(self, picking):
        """ Gets the partner that will be invoiced
            Note that this function is inherited in the sale and purchase modules
            @param picking: object of the picking for which we are selecting the partner to invoice
            @return: object of the partner to invoice
        """
        if picking.sale_id:
            return picking.sale_id.partner_id.id
        elif picking.purchase_id:
            return picking.purchase_id.partner_id.id
        else:
            return picking.partner_id and picking.partner_id.id

    def action_invoice_create(self, journal_id, group=False, move_type="out_invoice"):
        todo = {}
        for picking in self:
            partner = self._get_partner_to_invoice(picking)
            # grouping is based on the invoiced partner
            if group:
                key = partner
            else:
                key = picking.id
            for move in picking.move_ids:
                if move.picking_id.invoice_state == "2binvoiced":
                    if (move.state == "done") and not move.scrapped:
                        todo.setdefault(key, [])
                        todo[key].append(move)
        invoices = []
        for moves in todo.values():
            invoices += self._invoice_create_line(moves, journal_id, move_type)

        return invoices

    def _get_invoice_vals(self, key, inv_type, journal_id, move):
        partner, currency_id, company_id, user_id = key
        if inv_type in ("out_invoice"):
            account_id = partner.property_account_receivable_id.id
            payment_term = partner.property_payment_term_id.id or False
        else:
            account_id = partner.property_account_payable_id.id
            payment_term = partner.property_supplier_payment_term_id.id or False

        if move.purchase_line_id and move.purchase_line_id.order_id:
            purchase = move.purchase_line_id.order_id
            payment_term = purchase.payment_term_id.id

        sale = move.picking_id.sale_id

        inv_vals = {
            "ref": move.picking_id.name,
            "invoice_date": self.env.context.get("date_inv", False),
            "user_id": user_id,
            "partner_id": partner.id,
            "move_type": inv_type,
            "company_id": company_id,
            "currency_id": currency_id,
            "journal_id": journal_id,
        }
        if sale and inv_type in ("out_invoice"):
            inv_vals.update(
                {
                    "invoice_payment_term_id": sale.payment_term_id.id,
                    "user_id": sale.user_id.id,
                    "invoice_user_id": sale.user_id.id,
                    "team_id": sale.team_id.id,
                    "invoice_origin": sale.name,
                    "narration": sale.note,
                    "partner_shipping_id": sale.partner_shipping_id.id,
                    "carrier_id": sale.carrier_id.id or False,
                    "analytic_account_id": sale.analytic_account_id.id or False,
                    "division_type_id": sale.division_type_id.id or False,
                    "tracking_ref": sale.customer_sales_order or '',
                }
            )
        return inv_vals

    def _create_invoice_from_picking(self, picking, vals):
        """ This function simply creates the invoice from the given values. It is overriden in delivery module to add the delivery costs.
        """
        invoice_obj = self.env["account.move"]
        return invoice_obj.with_context(default_move_type="out_invoice").create(vals)

    def _invoice_create_line(self, moves, journal_id, inv_type="out_invoice"):
        invoice_obj = self.env["account.move"]
        move_obj = self.env["stock.move"]
        invoices = {}
        is_extra_move, extra_move_tax = move_obj._get_moves_taxes(moves, inv_type)
        product_price_unit = {}
        invoice_id = False

        for move in moves:
            company = move.company_id
            origin = move.picking_id.name
            partner, user_id, currency_id = move_obj._get_master_data(move, company)

            key = (partner, currency_id, company.id, user_id)
            invoice_vals = self._get_invoice_vals(key, inv_type, journal_id, move)

            if key not in invoices:
                # Get account and payment terms
                invoice_id = self._create_invoice_from_picking(
                    move.picking_id, invoice_vals
                )
                if move.picking_id.picking_type_code == 'outgoing':
                    invoice_id.picking_ids = [(4, move.picking_id.id)]
                invoices[key] = invoice_id.id
            else:
                invoice_id = invoice_obj.browse(invoices[key])
                if move.picking_id.picking_type_code == 'outgoing':
                    invoice_id.picking_ids = [(4, move.picking_id.id)]
                merge_vals = {}
                if not invoice_id.ref or invoice_vals["ref"] not in invoice_id.ref.split(", "):
                    invoice_origin = filter(None, [invoice_id.ref, invoice_vals["ref"]])
                    merge_vals["ref"] = ", ".join(invoice_origin)
                if invoice_vals.get("name", False) and (
                    not invoice_id.name
                    or invoice_vals["name"] not in invoice_id.name.split(", ")):
                    invoice_name = filter(None, [invoice_id.name, invoice_vals["name"]])
                    merge_vals["name"] = ", ".join(invoice_name)
                if merge_vals:
                    invoice_id.write(merge_vals)

            invoice_line_vals = move_obj._get_invoice_line_vals(move, partner, inv_type)
            invoice_line_vals["move_id"] = invoices[key]
            invoice_line_vals["ref"] = origin
            invoice_line_vals["sale_line_ids"] = [(6, 0, move.sale_line_id.ids)]
            invoice_line_vals["purchase_line_id"] = move.purchase_line_id.id

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
            invoice_id.write(
                {"invoice_line_ids": [(0, 0, invoice_line_vals)]}
            )
            move_data = self.env["account.move"].browse(invoices[key])

            if move.picking_id.picking_type_code == 'outgoing':
                move.picking_id.write({"invoice_state": "invoiced"})
            if invoice_id and move.picking_id.sale_id:
                invoice_id.pw_shipping_cost = move.picking_id.sale_id.pw_shipping_cost
        for inv_id in invoices.values():
            invoice = invoice_obj.browse(inv_id)
            for inv_line in invoice.invoice_line_ids:
                for move in moves:
                    if move.sale_line_id and move.sale_line_id.id in inv_line.sale_line_ids.ids:
                        move.sale_line_id.invoice_lines = [(4, inv_line.id)]

                    if move.purchase_line_id:
                        if inv_line.purchase_line_id.id == move.purchase_line_id.id:
                            move.purchase_line_id.invoice_lines = [(4, inv_line.id)]

            invoice._compute_amount()

        return invoices.values()

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        for picking in self:
            if picking.picking_sequence_code in ['IN_SGRN', 'IN'] and picking.purchase_id:
                vendor_bills = picking.purchase_id.invoice_ids.filtered(lambda inv: inv.state in ['draft', 'posted'])
                if vendor_bills:
                    vendor_bills.write({'picking_ids': [(4, picking.id)]})
        return res

