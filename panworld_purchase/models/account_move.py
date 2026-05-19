# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_round, float_compare


class AccountMove(models.Model):
    _inherit = "account.move"

    rma_done = fields.Boolean("RMA is Done", copy=False)
    po_ref_ids = fields.Many2many(comodel_name="purchase.order",
                                  relation="purchase_invoice_rel",
                                  column1="invoice_id",
                                  column2="purchase_id",
                                  string="PO Reference",
                                  help="Purchase Order Number")
    tracking_ref = fields.Char(string="Tracking Reference",
                               help="Tracking Reference")
    grn_tracking = fields.Char(string="Tracking(AWB)",
                               help="Tracking(AWB)")
    is_service_quotation_bill = fields.Boolean(string='Service Quotation Bill')
    customer_sales_order = fields.Char(string='Customer Sales Order')
    customer_name = fields.Char(string='Customer Name')
    boe_no = fields.Char(related='tracking_number_bill_id.boe_no', string='BOE No.')


    # def _compute_total_quantity(self):
    #     # Get total order product quantity.
    #     for rec in self:
    #         domain = [('move_id', '=', rec.id)]
    #         move_line = self.env['account.move.line']
    #         query = move_line._where_calc(domain)
    #         move_line._apply_ir_rules(query, 'read')
    #         from_clause, where_clause, where_clause_params = query.get_sql()
    #         where_str = where_clause and ("WHERE %s" % where_clause) or ''
    #         query_str = 'SELECT quantity FROM ' + from_clause + where_str
    #         from_clause, where_clause, where_clause_params = query.get_sql()
    #         self._cr.execute(query_str, where_clause_params)
    #         quantitys = [m_dict['quantity'] for m_dict in self.env.cr.dictfetchall()]
    #         rec.total_quantity = sum(quantitys)

    # @api.depends('invoice_line_ids.quantity')
    # def _compute_total_quantity(self):
    #     MoveLine = self.env['account.move.line']
    #     # init values
    #     for rec in self:
    #         rec.total_quantity = 0.0
    #     if not self.ids:
    #         return
    #
    #     # aggregate by move_id for all moves in self
    #     domain = [('move_id', 'in', self.ids)]
    #     grouped = MoveLine.read_group(domain, ['quantity'], ['move_id'])
    #     # grouped rows look like: {'move_id': (id, 'display_name'), 'quantity': <sum>}
    #     totals = {g['move_id'][0]: (g.get('quantity') or 0.0) for g in grouped if g.get('move_id')}
    #     for rec in self:
    #         rec.total_quantity = totals.get(rec.id, 0.0)


    def action_post(self):
        # Validation checks
        for rec in self:
            if (
                    rec.move_type in ("in_invoice", "in_refund", "in_receipt")
                    and rec.bill_difference_amount != 0 and not rec.is_shipping_service
            ):
                raise ValidationError(_("Bill Difference Amount must be zero!"))

        payment_references = {move.id: move.payment_reference for move in self}
        result = super(AccountMove, self).action_post()

        for move in self:
            # Restore payment references if needed
            if move.id in payment_references:
                move.payment_reference = payment_references[move.id]

        return result

    @api.model_create_multi
    def create(self, vals_list):
        moves = super(AccountMove, self).create(vals_list)
        for move in moves:
            if move.move_type == 'in_invoice':
                move._check_and_update_po_received_qty()
        return moves

    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        if 'invoice_line_ids' in vals or 'state' in vals:
            for move in self:
                if move.move_type == 'in_invoice':
                    move._check_and_update_po_received_qty()
        return res

    def _check_and_update_po_received_qty(self):
        for move in self:
            if move.move_type == 'in_invoice' and move.state == 'draft':
                po_line_inv_lines = move.invoice_line_ids.filtered(lambda l: l.purchase_line_id)
                if not po_line_inv_lines:
                    continue

                all_match = True
                for line in po_line_inv_lines:
                    if float_compare(line.quantity, line.purchase_line_id.po_qty, precision_rounding=line.product_uom_id.rounding or 0.01) != 0:
                        all_match = False
                        break

                if all_match:
                    for line in po_line_inv_lines:
                        line.purchase_line_id.to_be_received_qty = 0.0


    @api.model
    def _search(self, args, offset=0, limit=None, order=None, **kwargs):
        if self.env.context.get('my_context') and self.env.context.get('stock_picking_id'):
            picking = self.env['stock.picking'].browse(self.env.context.get('stock_picking_id'))
            # if picking and picking.purchase_id and picking.purchase_id.invoice_ids:
            #     args += ['&', '&', ('move_type', '=', 'in_invoice'), ('is_shipping_service', '=', False), '|',
            #              ('partner_id', '=', picking.purchase_id.partner_id.id), ('name', '=', 'Not Available1')]
            if picking and picking.partner_id and not picking.purchase_id:
                args += ['&', '&', ('move_type', '=', 'in_invoice'), ('is_shipping_service', '=', False), '|',
                         ('partner_id', '=', picking.partner_id.id), ('name', '=', 'Not Available1')]
            else:
                args += [('name', '=', 'Not Available1'), ('move_type', '=', 'in_invoice'), ('partner_id', '!=', False)]
        elif self.env.context.get('my_context') and self.env.context.get('my_partner_id') and not self.env.context.get('stock_picking_id'):
            args += ['&', '&', ('move_type', '=', 'in_invoice'), ('is_shipping_service', '=', False), '|',
                     ('partner_id', '=', self.env.context.get('my_partner_id')), ('name', '=', 'Not Available1')]
        elif self.env.context.get('my_context') and not self.env.context.get('my_partner_id') and not self.env.context.get('stock_picking_id'):
            args += [('name', '=', 'Not Available1'), ('move_type', '=', 'in_invoice'), ('partner_id', '!=', False)]
        res = super(AccountMove, self)._search(args, offset, limit, order)
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        # For Filtering the Related Bills Based on Vendor and Dummy Vendor Bill. 02/02/2024
        if self.env.context.get('my_context') and self.env.context.get('stock_picking_id'):
            picking = self.env['stock.picking'].browse(self.env.context.get('stock_picking_id'))
            if picking and picking.purchase_id and picking.purchase_id.invoice_ids:
                domain += ['&', '&', ('move_type', '=', 'in_invoice'), ('is_shipping_service', '=', False), '|',
                           ('partner_id', '=', picking.purchase_id.partner_id.id), ('name', '=', 'Not Available1')]
            elif picking and picking.partner_id and not picking.purchase_id:
                domain += ['&', '&', ('move_type', '=', 'in_invoice'), ('is_shipping_service', '=', False), '|',
                           ('partner_id', '=', picking.partner_id.id), ('name', '=', 'Not Available1')]
            else:
                domain += [('name', '=', 'Not Available1'), ('move_type', '=', 'in_invoice'),
                           ('partner_id', '!=', False)]
        elif self.env.context.get('my_context') and self.env.context.get('my_partner_id') and not self.env.context.get('stock_picking_id'):
            domain += ['&', '&', ('move_type', '=', 'in_invoice'), ('is_shipping_service', '=', False), '|',
                     ('partner_id', '=', self.env.context.get('my_partner_id')), ('name', '=', 'Not Available1')]
        elif self.env.context.get('my_context') and not self.env.context.get('my_partner_id') and not self.env.context.get('stock_picking_id'):
            domain += [('name', '=', 'Not Available1'), ('move_type', '=', 'in_invoice'), ('partner_id', '!=', False)]

        return super(AccountMove, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                   orderby=orderby,
                                                   lazy=lazy)


    @api.constrains('partner_id', 'ref')
    def _check_vendor_bill_partner_ref(self):
        """Method to avoid duplicate billing of vendor with same ref"""
        for move in self:
            if move.ref and move.move_type == 'in_invoice':
                duplicate_ref = self.search([
                    ('id', '!=', move.id),
                    ('partner_id', '=', move.partner_id.id),
                    ('ref', '=', move.ref),
                    ('move_type', '=', 'in_invoice')])
                if duplicate_ref:
                    raise ValidationError(
                        _("Bill for this vendor with same ref is already exist!"))


    @api.onchange('purchase_vendor_bill_id', 'purchase_id', 'po_ref_ids')
    def _onchange_purchase_auto_complete(self):
        super()._onchange_purchase_auto_complete()
        if self.move_type == 'in_invoice':
            grn_tracking_list = self.po_ref_ids._origin.filtered('carrier_tracking_ref').mapped('carrier_tracking_ref')
            tracking_ref_list = self.po_ref_ids._origin.filtered('customer_sales_order').mapped('customer_sales_order')
            self.update({
                'tracking_ref':','.join(tracking_ref_list),
                'grn_tracking': ','.join(grn_tracking_list)
                })

    @api.onchange('invoice_vendor_bill_id')
    def _onchange_invoice_vendor_bill(self):
        """ Overwrite the Auto-complete functionality by adding only the invoice lines with PO lines
        having 'To be received qty' is greater than zero"""
        if self.invoice_vendor_bill_id:
            # Copy invoice lines.
            for line in self.invoice_vendor_bill_id.invoice_line_ids.filtered(
                    lambda x: x.purchase_line_id.to_be_received_qty > 0):
                copied_vals = line.copy_data()[0]
                copied_vals['move_id'] = self.id
                new_line = self.env['account.move.line'].new(copied_vals)
                new_line.recompute_tax_line = True

            # Copy payment terms.
            self.invoice_payment_term_id = self.invoice_vendor_bill_id.invoice_payment_term_id

            # Copy currency.
            if self.currency_id != self.invoice_vendor_bill_id.currency_id:
                self.currency_id = self.invoice_vendor_bill_id.currency_id
                self._onchange_currency()

            # Reset
            self.invoice_vendor_bill_id = False
            self._recompute_dynamic_lines()

    def _add_purchase_order_lines(self, purchase_order_lines):
        """ Creates new invoice lines from purchase order lines -- custom
        Overwrite the Auto-complete functionality by adding only the invoice lines with PO lines
        having 'To be received qty' is greater than zero"""
        self.ensure_one()
        new_line_ids = self.env['account.move.line']

        for po_line in purchase_order_lines.filtered(lambda x: x.to_be_received_qty > 0):
            new_line_values = po_line._prepare_account_move_line(self)
            new_line_ids += self.env['account.move.line'].new(new_line_values)

        self.invoice_line_ids += new_line_ids

