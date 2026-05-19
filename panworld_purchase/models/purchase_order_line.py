# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo.exceptions import UserError,ValidationError
from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    barcode = fields.Char(related='product_id.barcode', string='ISBN')
    invoice_ref = fields.Char(compute="_compute_bill_ref_date", string='Bill Reference/Bill Date')
    customer_sales_order = fields.Char(string='Customer Sales Order')
    # customer_sales_order = fields.Char(string='Customer Sales Order', compute='_compute_customer_sales_order')
    customer_name = fields.Char(string='Customer Name', related="related_so.partner_id.name")
    remarks = fields.Char()
    related_so = fields.Many2one(comodel_name='sale.order', string='Related SO')
    name = fields.Text(string='Description', compute='_compute_product_name', store=True,
        readonly=False)

    @api.depends('product_id')
    def _compute_product_name(self):
        for line in self:
            if line.product_id:
                line.name = line.product_id.display_name
                line.date_planned = line.order_id.date_planned

    @api.depends("list_price", "po_qty", "po_price", "tax_ids")
    def _compute_amount(self):
        return super()._compute_amount()

    # def _get_discounted_price_unit(self):
    #     self.ensure_one()
    #     if self.discount:
    #         p_unit = (self.list_price * (1 - self.discount / 100))
    #         dis_price = round(p_unit, 2)
    #         if not float_is_zero(self.price_unit - dis_price, precision_digits=2):
    #             self.price_unit = dis_price
    #     else:
    #         if not float_is_zero(self.price_unit - self.list_price, precision_digits=2):
    #             self.price_unit = self.list_price
    #     return self.price_unit

    def _compute_bill_ref_date(self):
        for rec in self:
            rec.invoice_ref = ''
            coma = False
            if len(rec.order_id.invoice_ids) > 1:
                coma = True
            for inv in rec.order_id.invoice_ids:
                inv_name = "inv.display_name"
                if inv.invoice_date:
                    inv_date = inv.invoice_date
                else:
                    inv_date = inv.date
                if coma:
                    rec.invoice_ref += inv.display_name + " : " + fields.Date.to_string(inv_date) + ' , '
                else:
                    rec.invoice_ref = inv.display_name + " : " + fields.Date.to_string(inv_date)


    @api.depends('related_so')
    def _compute_customer_sales_order(self):
        for record in self:
            record.customer_sales_order = record.related_so.customer_sales_order

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            # related SO mandatory for 'Can be sold' enabled products only
            product = self.env['product.product'].browse(int(values['product_id']))
            sellable_product = product.sale_ok
            if 'related_so' in values and not values['related_so'] and sellable_product:
                raise UserError('Related SO Required! \nYou must provide a value for Related SO.')
        lines = super(PurchaseOrderLine, self).create(vals_list)
        return lines

    #
    def write(self, vals_list):
        if 'related_so' in vals_list and not vals_list['related_so']:
            raise UserError('Write : Related SO Required! \nYou must provide a value for Related SO.')
        result = super(PurchaseOrderLine, self).write(vals_list)
        return result

    def _prepare_account_move_line(self, move=False):
        vals = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        vals["customer_name"] = self.customer_name
        vals["customer_sales_order"] = self.customer_sales_order
        return vals

    # @api.onchange('discount', 'list_price')
    # def _onchange_discount(self):
    #     """calculate price unit when change discount from wizard T04425"""
    #     if self.discount:
    #         self.price_unit = (self.list_price * (1 - self.discount / 100))
    #     else:
    #         self.price_unit = self.list_price

    # @api.onchange('product_qty', 'product_uom_id')
    # def _onchange_quantity(self):
    #     discount = self.discount
    #     list_price = self.list_price
    #     price_unit = self.price_unit
    #     price_subtotal = self.price_subtotal
    #     if not self.product_id:
    #         return
    #     # super()._onchange_quantity()
    #     self.list_price = self._get_discounted_price_unit()
    #     self.discount = discount
    #     self.list_price = list_price
    #     self.price_unit = price_unit
    #     self.price_subtotal = price_subtotal

    def _get_po_line_moves(self):
        self.ensure_one()
        res = super()._get_po_line_moves()
        return res.filtered(lambda x: not x.location_dest_id.is_shipper_location)

    def _prepare_stock_move_vals(
            self, picking, price_unit, product_uom_qty, product_uom_id):
        # Override this method to pass panworld custom fields, and change the destination picking as ready state
        # shipping for newly added products in the PO.
        self.ensure_one()
        ready_shipping_id = self.order_id.picking_ids.filtered(
            lambda x: x.location_dest_id.is_shipper_location and x.state == 'assigned')[:1]
        if ready_shipping_id:
            picking = ready_shipping_id
        res = super(PurchaseOrderLine, self)._prepare_stock_move_vals(
            picking, price_unit, product_uom_qty, product_uom_id)
        res.update({
            'customer_name': self.customer_name or '',
            'customer_sales_order': self.customer_sales_order or '',
        })
        return res

    @api.model
    def default_get(self, fields):
        """Set the default tax for PO lines as the default Purchase Tax"""
        res = super().default_get(fields)
        company = self.env.company
        if company.account_purchase_tax_id:
            res['tax_ids'] = [(6, 0, [company.account_purchase_tax_id.id])]
        return res
