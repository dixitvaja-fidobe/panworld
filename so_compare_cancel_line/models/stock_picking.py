# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
import datetime

from odoo.orm.commands import Command

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # def button_validate(self):
    #     _logger.info("------------- button_validate start so_compare_cancel_line/models/stock_picking.py ------------",datetime.datetime.now())
    #     res = super(StockPicking, self).button_validate()
    #     for rec in self:
    #         if rec.sale_id:
    #             if rec.sale_id.state not in ('sale', 'done'):
    #                 raise UserError(_('Please Confirm Sale Order to Validate this Picking.'))
    #             sale_order_id = rec.sale_id
    #             if rec.state == 'done' and self.env.user.has_group('so_compare_cancel_line.create_invoice_of_multiple_pickings_group') and rec.picking_type_id.code == 'outgoing' and rec.location_id.usage == 'internal':
    #                 wiz = self.env['sale.advance.payment.inv'].with_company(rec.company_id).with_context(active_ids=[sale_order_id.id],open_invoices=True,custom_picking_id=rec.id).create({})
    #                 inv = wiz.with_company(rec.company_id).create_invoices()
    #                 invoice = rec.sale_id.invoice_ids.browse(inv.get('res_id'))
    #                 invoice.picking_ids = [Command.set([rec.id])]
    #     return res

    def button_validate(self):
        # 1️⃣ Fail fast
        invalid = self.filtered(
            lambda p: p.sale_id and p.sale_id.state not in ('sale', 'done')
        )
        if invalid:
            raise UserError(_('Please Confirm Sale Order to Validate this Picking.'))

        # 2️⃣ Validate picking FIRST (fast response)
        res = super().button_validate()

        # 3️⃣ Permission check
        if not self.env.user.has_group(
                'so_compare_cancel_line.create_invoice_of_multiple_pickings_group'
        ):
            return res

        # 4️⃣ Eligible pickings
        eligible = self.filtered(lambda p:
                                 p.state == 'done'
                                 and p.sale_id
                                 and p.picking_type_id.code == 'outgoing'
                                 and p.location_id.usage == 'internal'
                                 )

        if not eligible:
            return res

        # 5️⃣ Create invoices grouped by Sale Order
        eligible._create_invoices_for_pickings()

        return res

    def _create_invoices_for_pickings(self):
        SaleAdvance = self.env['sale.advance.payment.inv']

        # Group pickings by sale order
        so_to_pickings = {}
        for picking in self:
            so_to_pickings.setdefault(picking.sale_id, []).append(picking)

        for sale, pickings in so_to_pickings.items():
            picking_ids = [p.id for p in pickings]

            # Pre-calculate moves by line to optimize _prepare_invoice_line
            # This avoids O(N^2) complexity in large orders
            moves_by_line = {}
            for picking in pickings:
                for move in picking.move_ids:
                    if move.state == 'done' and move.sale_line_id:
                        moves_by_line.setdefault(move.sale_line_id.id, []).append(move.id)

            # Create ONE invoice for all pickings of this SO validated together
            wiz = SaleAdvance.with_company(sale.company_id).with_context(
                active_ids=[sale.id],
                open_invoices=True,
                custom_picking_id=picking_ids,
                custom_moves_by_line=moves_by_line,
            ).create({})

            action = wiz.create_invoices()
            if action and action.get('res_id'):
                invoice = self.env['account.move'].browse(action['res_id'])
                # Link all pickings to this invoice
                invoice.write({
                    'picking_ids': [Command.link(pid) for pid in picking_ids]
                })



