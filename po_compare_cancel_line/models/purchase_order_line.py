# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
import logging
from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError,ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
_logger = logging.getLogger(__name__)

class PurchaseOrderLineCustom(models.Model):
    _inherit = 'purchase.order.line'

    list_price = fields.Float(
        string="List Price", related="po_list_price", digits='Product Price')
    price_unit = fields.Float(string='Bill Price', digits='Product Price', readonly=True, store=True)
    rfq_qty = fields.Float(string='RFQ Quantity', default=1)
    po_qty = fields.Float(string='PO Quantity', compute="_compute_po_qty", store=True, default=0.0)
    to_be_received_qty = fields.Float(string='To Be Received QTY', default=0, help="For The First Time 'To Be Received Qty' is Equal To 'Po Qty' ")
    po_price = fields.Float(string='PO Price', default=0, compute="_compute_po_price", store=True)
    po_target_price = fields.Float(string="PO Target Price")
    cancel_qty = fields.Float('Canceled Qty', copy=False)
    po_list_price = fields.Float(
        string=' Po List Price',
        required=False
    )
    po_discount = fields.Float(
        string=' Po Discount(%)',
        required=False
    )
    po_subtotal = fields.Float(
        string=' Po Subtotal',
        required=False,
        compute="_compute_po_subtotal",
        store=True
    )
    isbn = fields.Char(related="product_id.barcode")
    customer_sales_order = fields.Char(string='Customer Sales Order')
    customer_name = fields.Char(string='Customer Name')
    remarks = fields.Char()
    cancel_reason = fields.Selection(string="Cancel Reason", selection=[
        ('forthcoming', 'Forthcoming'), ('out_of_print', 'Out Of Print'),
        ('out_of_stock', 'Out Of Stock'), ('print_on_demand', 'Print On Demand'),
        ('new_edition', 'New Edition'), ('discontinued', 'Discontinued'),
        ('vendor_change', 'Vendor Change'), ('rights_restricted', 'Rights Restricted'),
        ('bundle_book', 'Bundle Book'), ('market_restricted', 'Market Restricted'),
        ('sale_restricted', 'Sale Restricted'), ('back_order', 'Back Order'),
        ('reprinting', 'Reprinting'), ('minimum_qty_amount_required', 'Minimum Qty/Amount Required'),
        ('price_change', 'Price Change'), ('unavailable', 'Unavailable'),('short_rcvd', 'Shortage Received'),
        ('oos', 'OOS Delivered'), ('replaced', 'Replaced in another Order')],copy=False)
    # cancel_reason = fields.Text("Cancel Reason", copy=False)
    new_partner_id = fields.Many2one('res.partner', string='Vendor',
                                     help="You can find a vendor by its Name, TIN, Email or Internal Reference.",
                                     copy=False)
    action = fields.Selection(string="Action",
                              selection=[('backorder', 'Backorder'), ('reorder', 'Reorder'), ('cancel', 'Cancel')],
                              required=False, copy=False)
    product_qty = fields.Float(string='Vendor Bill Qty', digits='Product Unit of Measure', default=0, compute="_compute_po_qty", store=True)

    @api.depends("po_list_price", "po_price")
    def _compute_price_unit_and_date_planned_and_name(self):
        super()._compute_price_unit_and_date_planned_and_name()
        for line in self:
            if line.po_list_price:
                line.price_unit = line.po_list_price
            elif line.po_price:
                line.price_unit = line.po_price

    @api.onchange('product_id')
    def _onchange_product_id_set_list_price(self):
        for line in self:
            if line.product_id:
                line.po_list_price = line.product_id.lst_price

    @api.depends("product_qty", "price_unit", "tax_ids", "discount")
    def _compute_amount(self):
        return super()._compute_amount()

    @api.depends('rfq_qty', 'cancel_qty')
    def _compute_po_qty(self):
        for rec in self:
            rec.po_qty = rec.rfq_qty - (rec.cancel_qty or 0.0)
            rec.product_qty = rec.po_qty

    @api.onchange('po_qty')
    def onchange_update_to_be_received_qty(self):
        for rec in self:
            if rec.order_id.state == 'draft':
                rec.to_be_received_qty = rec.rfq_qty - rec.cancel_qty

    @api.depends('invoice_lines.move_id.state', 'invoice_lines.quantity', 'qty_received', 'product_uom_qty',
                 'order_id.state', 'to_be_received_qty')
    def _compute_qty_invoiced(self):
        for line in self:
            # compute qty_invoiced
            qty = 0.0
            for inv_line in line._get_invoice_lines():
                if inv_line.move_id.state not in ['cancel'] or inv_line.move_id.payment_state == 'invoicing_legacy':
                    if inv_line.move_id.move_type == 'in_invoice':
                        qty += inv_line.product_uom_id._compute_quantity(inv_line.quantity, line.product_uom_id)
                    elif inv_line.move_id.move_type == 'in_refund':
                        qty -= inv_line.product_uom_id._compute_quantity(inv_line.quantity, line.product_uom_id)
            line.qty_invoiced = qty

            # compute qty_to_invoice
            if line.order_id.state in ['purchase', 'done']:
                if line.product_id.purchase_method == 'purchase':
                    line.qty_to_invoice = (line.to_be_received_qty + line.qty_invoiced) - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_received - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    # Have to uncomment this code on 16th Jan 2024 as per client requirement.
    # Comment this code as per client request by Hala on 4th April 2024 due to not getting this validation warning mesg.
    # @api.constrains("po_qty", "product_qty")
    # def _check_po_qty(self):
    #     for pol in self:
    #         if pol.po_qty < pol.product_qty:
    #             raise ValidationError(_('You can not set Vendor Bill Qty more then PO Quantity'))
    #         elif pol.qty_invoiced + pol.to_be_received_qty > pol.po_qty:
    #             raise ValidationError(_('You can not set Vendor Bill Qty more then PO Quantity'))



    @api.depends(
        "po_qty",
        "po_price"
    )
    def _compute_po_subtotal(self):
        for rec in self:
            subtotal = rec.po_price * rec.po_qty
            rec.po_subtotal = rec.order_id.currency_id.round(subtotal)

    @api.depends(
        "po_list_price",
        "po_discount",
    )
    def _compute_po_price(self):
        for rec in self:
            if rec.po_list_price:
                rec.po_price = rec.po_list_price - (rec.po_list_price * rec.po_discount / 100)
            else:
                rec.po_price = 0



    @api.onchange('action')
    def onchange_action(self):
        """Remove existing values for vendor and cancel_reason fields as per selected action"""
        if self.action == 'reorder':
            self.cancel_reason = False
        elif self.action == 'cancel':
            self.new_partner_id = False
        else:
            self.new_partner_id = False
            self.cancel_reason = False

    @api.onchange('cancel_qty')
    def _onchange_cancel_qty(self):
        for rec in self:
            if rec.cancel_qty > 0 and not rec.cancel_reason:
                return {'warning': {
                    'title': 'Warning!',
                    'message': 'Cancel Reason Required!',
                    'type': 'danger',  # You can also use 'danger' for an error message
                }}



    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        res = super()._prepare_stock_move_vals(picking=picking, price_unit=price_unit, product_uom_qty=product_uom_qty,
                                               product_uom=product_uom)
        qty = self._get_qty_procurement()
        if self.env.context.get('action_backorder'):
            res.update({'product_uom_qty': abs(self.po_qty - self.product_qty)})
        else:
            res.update({'product_uom_qty': abs(self.product_qty)})
        return res

    def _prepare_stock_moves(self, picking):
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        # customization start
        if self.env.context.get('action_backorder'):
            diff_qty = abs(self.product_qty - self.po_qty)
            product_uom_qty, product_uom = self.product_uom._adjust_uom_quantities(diff_qty, self.product_id.uom_id)
            res.append(self._prepare_stock_move_vals(picking, diff_qty, product_uom_qty, product_uom))
        # customization end
        else:
            price_unit = self._get_stock_move_price_unit()
            qty = self._get_qty_procurement()

            move_dests = self.move_dest_ids
            if not move_dests:
                move_dests = self.move_ids.move_dest_ids.filtered(
                    lambda m: m.state != 'cancel' and not m.location_dest_id.usage == 'supplier')

            if not move_dests:
                qty_to_attach = 0
                # customization
                if self.po_qty == self.product_qty:
                    qty_to_push = self.product_qty - qty
                else:
                    qty_to_push = self.po_qty - self.product_qty


            else:
                move_dests_initial_demand = self.product_id.uom_id._compute_quantity(
                    sum(move_dests.filtered(
                        lambda m: m.state != 'cancel' and not m.location_dest_id.usage == 'supplier').mapped(
                        'product_qty')),
                    self.product_uom, rounding_method='HALF-UP')
                qty_to_attach = move_dests_initial_demand - qty
                qty_to_push = self.product_qty - move_dests_initial_demand

            if float_compare(qty_to_attach, 0.0, precision_rounding=self.product_uom.rounding) > 0:
                product_uom_qty, product_uom = self.product_uom._adjust_uom_quantities(qty_to_attach,
                                                                                       self.product_id.uom_id)
                res.append(self._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom))
            if not float_is_zero(qty_to_push, precision_rounding=self.product_uom.rounding):
                product_uom_qty, product_uom = self.product_uom._adjust_uom_quantities(qty_to_push,
                                                                                       self.product_id.uom_id)
                extra_move_vals = self._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
                extra_move_vals['move_dest_ids'] = False  # don't attach
                res.append(extra_move_vals)
        return res

    def action_cancel_po_lines(self):
        self.write({'state': 'cancel'})

    def action_reorder(self):
        # reorder - create new PO
        purchase_order = self.env['purchase.order']
        reordered_vendors = set()
        for line in self:
            if not line.new_partner_id:
                raise UserError(_("Please select vendor!."))

            elif line.new_partner_id.id not in reordered_vendors:
                same_partner_lines = self.filtered(lambda x: x.new_partner_id == line.new_partner_id)
                new_po_lines = self.env['purchase.order.line']

                for l in same_partner_lines:
                    temp_line = l.copy()
                    temp_line.write({
                        'partner_id': l.new_partner_id.id,
                        'product_qty': abs(l.product_qty - l.po_qty),
                        'new_partner_id': False,
                        'action': False,
                        'state': 'draft'
                    })
                    new_po_lines |= temp_line
                _logger.info("\n New Purchase Order Lines %s \n", new_po_lines)

                new_po = purchase_order.create({
                    'partner_id': line.new_partner_id.id,
                    'order_line': new_po_lines.ids,
                    'origin': ",".join(list(set(same_partner_lines.order_id.mapped('name'))))
                })
                _logger.info("\n New Purchase Order %s Created with vendor %s \n", new_po.id, line.new_partner_id.name)
                reordered_vendors.add(line.new_partner_id.id)

