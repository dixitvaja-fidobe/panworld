# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################

from odoo import _, fields, models, api
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    rma_id = fields.Many2one("rma.ret.mer.auth", string="RMA")
    rma_done = fields.Boolean("RMA is Done", copy=False)
    partner_bill_ids = fields.Many2many("account.move", "rma_picking_invoice_rel",
                                        "rma_picking_id","related_invoice_id", string='Related bill(s)')
    valid_invoice_ids = fields.Many2many(
        "account.move",compute="_compute_valid_invoice_ids", store=False)

    @api.depends('rma_id.sale_order_id.invoice_ids')
    def _compute_valid_invoice_ids(self):
        """
        Fetch all the Invoices created for the selected sale order tagged in the RMA picking
        """
        for record in self:
            sale_order = record.rma_id.sale_order_id
            record.valid_invoice_ids = sale_order.invoice_ids if sale_order else [(5, 0, 0)]

    def _action_done(self):
        # Don't allow to validate outgoing picking before validating incoming in case of exchange.
        for picking in self.filtered(lambda p: p.rma_id):
            incoming_pickings = picking.rma_id.stock_picking_ids.filtered(
                lambda p: p.picking_type_code == "incoming" and p.id != picking.id
            )
            if incoming_pickings and any(p.state != "done" for p in incoming_pickings):
                raise UserError(
                    _(
                        "Outgoing picking cannot be done before validating incoming picking."
                    )
                )
        res = super(StockPicking, self)._action_done()
        # Unlink return picking created by odoo, when exchange of products.
        to_remove = self.env['stock.picking']
        eligible_pickings = self.filtered(
            lambda p: p.picking_type_code == "outgoing"
            and p.rma_id
            and p.rma_id.sale_order_id
            and p.sale_id
        )
        for picking in eligible_pickings:
            sale_order = picking.sale_id
            warehouse = sale_order.warehouse_id
            if warehouse:
                return_picking_type = warehouse.return_type_id
                to_remove |= sale_order.picking_ids.filtered(
                    lambda p: p.picking_type_id.id == return_picking_type.id
                    and p.state not in ["done", "cancel"]
                )

        if to_remove:
            to_remove.sudo().action_cancel()
            to_remove.sudo().unlink()
        return res


