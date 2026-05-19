# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################


from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_compute_cost_from_sheet = fields.Boolean(
        string="Compute cost from sheet",
        help="Compute cost (MCO, SCO and OCO) base on sheet",
    )

    @api.depends("order_id.partner_id", "price_subtotal", "order_id.customer_so_date")
    def _compute_marketplace_cost(self):
        # Override method to set marketplace cost base on excel file data.
        for rec in self:
            if rec.is_compute_cost_from_sheet:
                return True
        return super()._compute_marketplace_cost()

    @api.depends("order_id.pick_type", "order_id.total_weight", "order_id.carrier_id")
    def _compute_shipping_cost(self):
        # Override method to set shipping cost base on excel file data.
        for rec in self:
            if rec.is_compute_cost_from_sheet:
                return True
        return super()._compute_shipping_cost()

    @api.depends("order_id.partner_id", "price_subtotal", "order_id.customer_so_date")
    def _compute_other_cost(self):
        # Override method to set other cost base on excel file data.
        for rec in self:
            if rec.is_compute_cost_from_sheet:
                return True
        return super()._compute_other_cost()


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        # Add panworld custom fields values in invoice for (regular invoice).
        vals = super()._prepare_invoice()
        delivery_note = False
        if self.env.context.get('button_validate_picking_ids'):
            delivery_note = self.env['stock.picking'].browse(self.env.context.get('button_validate_picking_ids'))
        elif self.env.context.get('custom_picking_id'):
            delivery_note = self.env['stock.picking'].browse(self.env.context.get('custom_picking_id'))
        if delivery_note:
            delivery_note = delivery_note.filtered(lambda x: x.picking_type_code == 'outgoing')
            if delivery_note:
                delivery_note = delivery_note[0]
                vals.update({
                    'invoice_date':
                        delivery_note.scheduled_date,
                        # self.customer_so_date if self.is_imported else self.date_order,
                })
        return vals

    def action_confirm(self):
        res = super().action_confirm()
        # Add panworld custom fields values.
        for rec in self:
            rec.picking_ids.write({
                "scheduled_date":
                    rec.customer_so_date if rec.is_imported else rec.date_order,
                "date_deadline":
                    rec.customer_so_date if rec.is_imported else rec.date_order,
            })
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self, **optional_values):
        # Add panworld custom fields values in invoice for (regular invoice).
        vals = super()._prepare_invoice_line(**optional_values)
        if self.is_compute_cost_from_sheet:
            vals.update({
                'is_compute_cost_from_sheet': True,
                'marketplace_cost': self.marketplace_cost,
                'shipping_cost': self.shipping_cost,
                'other_cost': self.other_cost
            })
        return vals

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_compute_cost_from_sheet = fields.Boolean(
        string="Compute cost from sheet",
        help="Compute cost (MCO, SCO and OCO) base on sheet",
    )

    @api.depends('move_id.partner_id', 'price_subtotal', 'move_id.invoice_date')
    def _compute_marketplace_cost(self):
        # Override method to set marketplace cost base on excel file data.
        for rec in self:
            if rec.is_compute_cost_from_sheet:
                return True
        return super()._compute_marketplace_cost()

    @api.depends('move_id.pw_shipping_cost')
    def _compute_shipping_cost(self):
        # Override method to set shipping cost base on excel file data.
        for rec in self:
            if rec.is_compute_cost_from_sheet:
                return True
        return super()._compute_shipping_cost()

    @api.depends('move_id.partner_id', 'price_subtotal', 'move_id.invoice_date')
    def _compute_other_cost(self):
        # Override method to set other cost base on excel file data.
        for rec in self:
            if rec.is_compute_cost_from_sheet:
                return True
        return super()._compute_other_cost()
