# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # @api.model
    # def _default_journal_account(self):
    #     journal_id = self.env.context.get('journal_id')
    #     print('kkkkkkkkkkkkkkkkk',self.env.context)
    #     journal_default_acc = False
    #     if journal_id:
    #         journal_id_brw = self.env['account.journal'].browse(journal_id)
    #         if journal_id_brw and journal_id_brw.default_account_id:
    #             journal_default_acc = journal_id_brw.default_account_id.id
    #     return journal_default_acc

    weight = fields.Float(
        related='product_id.weight', string='Weight (in g)', help='Product weight')
    total_weight = fields.Float(
        compute='_compute_total_weight', string='Total Weight (in g)',
        help='Total product weight base on product quantity', store=True)
    list_price = fields.Float(
        string="List Price", digits='Product Price',
        help='Unit price (after discount)')
    remarks = fields.Char(string='Remarks')
    landed_cost = fields.Float(
        compute='_compute_landed_cost', string='LCO', help='Landed cost', store=True)
    marketplace_cost = fields.Float(
        compute='_compute_marketplace_cost', string='MCO',
        help='Marketplace cost base on configuration in customer', store=True)
    shipping_cost = fields.Float(
        compute='_compute_shipping_cost', string='SCO',
        help='Shipping cost base on product total weight', store=True)
    other_cost = fields.Float(
        compute='_compute_other_cost', string='OCO',
        help='Other cost base on configuration in customer', store=True)
    subtotal_cost = fields.Float(
        compute='_compute_subtotal_cost', string='TCO (Subtotal)',
        help='Subtotal cost base on SCO, MCO, OCO and LCO', store=True)
    gp_percentage = fields.Float(
        compute='_compute_gp_percentage', string='GP%',
        help='GP percentage base on subtotal and TCO subtotal', store=True)
    shipping_term_id = fields.Many2one('shipping.term', string="Shipping Term")
    shipping_date = fields.Date(
        string='Shipping Date', help='Shipping date for shipping service lines')
    track_number = fields.Char(
        string='Track No', help='Track no for shipping service lines')
    be_number = fields.Char(
        string='BE No', help='BE no for shipping service lines')
    shipping_service_partner_id = fields.Many2one('res.partner', string='Vendor')
    vendor_bill_ref = fields.Char(
        string='Vendor Bill Ref', help='Vendor bill ref for shipping service lines')
    shipping_service_weight = fields.Float(
        string='Weight- Kgs', help='Weight- kgs for shipping service lines')
    freight_amount = fields.Float(
        string='Freight Amount', help='Freight amount for shipping service lines')
    insurance_amount = fields.Float(
        string='Insurance Amount', help='Insurance amount for shipping service lines')
    admin_amount = fields.Float(
        string='Admin Amount', help=' Admin amount for shipping service lines')
    fuel_sur_amount = fields.Float(
        string='Fuel Sur', help='Fuel sur amount for shipping service lines')
    other_amount = fields.Float(
        string='Other Amount', help='Other amount for shipping service lines')
    course_id = fields.Char(string='Course ID', help='Course ID for Sharjah University')
    crn = fields.Char(string='CRN', help='CRN for Sharjah University')
    # account_id = fields.Many2one('account.account', string='Account',
    #                              index=True, ondelete="cascade",
    #                              domain="[('deprecated', '=', False), ('account_type', '!=', 'off_balance')]",
    #                              check_company=True,
    #                              tracking=True)
    oos_cost = fields.Float(compute="_compute_cost_for_oos", string="Cost for OOS", store=True)

    @api.depends('move_id.related_bill_ids', 'move_id.related_bill_ids.invoice_line_ids.price_unit',
                 'move_id.related_bill_ids.invoice_line_ids.product_id')
    def _compute_cost_for_oos(self):
        """To populate the cost of products for the Customer invoices with 'Out of Scope' journal"""
        for invoice_line in self:
            cost = 0.0
            move = invoice_line.move_id
            if (move.move_type == 'out_invoice' and move.journal_id.out_of_scope and
                    invoice_line.product_id and move.related_bill_ids):
                # Get all related bill lines with the same product
                matched_bill_lines = move.related_bill_ids.mapped('invoice_line_ids').filtered(
                    lambda l: l.product_id == invoice_line.product_id
                )
                if matched_bill_lines:
                    cost = matched_bill_lines[0].list_price
            invoice_line.oos_cost = cost

    @api.depends('product_id', 'quantity')
    def _compute_total_weight(self):
        # Get total weight of product base on (product weight and qty).
        for rec in self:
            rec.total_weight = rec.product_id.weight * rec.quantity

    @api.depends("quantity", "product_id")
    def _compute_landed_cost(self):
        for rec in self:
            rec.landed_cost = 0.0
            move = rec.move_id
            rma = move.rma_id
            if not rma:
                continue

            if not rma.is_imported and rma.rma_type == "customer":
                # Fallback to standard price only for local customer RMAs
                rec.landed_cost = rec.product_id.standard_price * rec.quantity
            elif rma.rma_type in ["customer", "sale_direct"] or rma.is_imported:
                # Direct relationship access is optimized by Odoo prefetching
                if rma.rma_type == "customer":
                    rec.landed_cost = rec.rma_sale_line_id.landed_cost or 0.0
                else:
                    rec.landed_cost = rec.rma_sale_direct_line_id.landed_cost or 0.0

    @api.depends('move_id.partner_id', 'price_subtotal', 'move_id.invoice_date')
    def _compute_marketplace_cost(self):
        for rec in self:
            rec.marketplace_cost = 0.0
            move = rec.move_id
            rma = move.rma_id
            if not rma:
                continue

            if move.invoice_date and move.partner_id and (not rma.is_imported and rma.rma_type == "customer"):
                rec.marketplace_cost = rec.price_subtotal * \
                    move.partner_id._get_marketplace_other_cost(
                        date_order=move.invoice_date
                    ).get('marketplace_cost') / 100.0
            elif rma.rma_type in ["customer", "sale_direct"] or rma.is_imported:
                if rma.rma_type == "customer":
                    rec.marketplace_cost = rec.rma_sale_line_id.marketplace_cost or 0.0
                else:
                    rec.marketplace_cost = rec.rma_sale_direct_line_id.marketplace_cost or 0.0

    @api.depends('move_id.pw_shipping_cost', 'move_id.total_weight')
    def _compute_shipping_cost(self):
        for rec in self:
            rec.shipping_cost = 0.0
            move = rec.move_id
            rma = move.rma_id
            if not rma:
                continue

            if move.total_weight > 0 and (not rma.is_imported and rma.rma_type == "customer"):
                rec.shipping_cost = (
                    move.pw_shipping_cost / move.total_weight
                ) * rec.total_weight
            elif rma.rma_type in ["customer", "sale_direct"] or rma.is_imported:
                if rma.rma_type == "customer":
                    rec.shipping_cost = rec.rma_sale_line_id.shipping_cost or 0.0
                else:
                    rec.shipping_cost = rec.rma_sale_direct_line_id.shipping_cost or 0.0

    @api.depends('move_id.partner_id', 'price_subtotal', 'move_id.invoice_date')
    def _compute_other_cost(self):
        for rec in self:
            rec.other_cost = 0.0
            move = rec.move_id
            rma = move.rma_id
            if not rma:
                continue

            if move.invoice_date and move.partner_id and (not rma.is_imported and rma.rma_type == "customer"):
                rec.other_cost = rec.price_subtotal * \
                    move.partner_id._get_marketplace_other_cost(
                        date_order=move.invoice_date
                    ).get('other_cost') / 100.0
            elif rma.rma_type in ["customer", "sale_direct"] or rma.is_imported:
                if rma.rma_type == "customer":
                    rec.other_cost = rec.rma_sale_line_id.other_cost or 0.0
                else:
                    rec.other_cost = rec.rma_sale_direct_line_id.other_cost or 0.0

    @api.depends(
        'shipping_cost', 'marketplace_cost', 'other_cost', 'landed_cost')
    def _compute_subtotal_cost(self):
        # Get TCO (Subtotal) base on (SCO, MCO, OCO and LCO).
        for rec in self:
            rec.subtotal_cost = rec.shipping_cost + rec.marketplace_cost + \
                rec.other_cost + rec.landed_cost

    @api.depends('price_subtotal', 'subtotal_cost')
    def _compute_gp_percentage(self):
        # Get GP% base on (subtotal and TCO subtotal).
        gp_percentage = 0.0
        for rec in self:
            if rec.price_subtotal > 0:
                gp_percentage = (
                    rec.price_subtotal - rec.subtotal_cost
                ) / rec.price_subtotal * 100.0
            rec.gp_percentage = gp_percentage


    @api.onchange('product_uom_id', 'quantity', 'discount', 'price_unit')
    def _onchange_product_uom_discount_price_unit(self):
        # Get unit price base on list price and discount
        for rec in self:
            list_price = rec.price_unit
            if rec.discount:
                list_price = rec.price_unit - (
                    rec.price_unit * rec.discount / 100.0)
            rec.list_price = list_price

    def _get_custom_shipping_service_total(self):
        # Get sum of shipping service lines amount
        for rec in self:
            total = sum([
                rec.freight_amount, rec.insurance_amount, rec.admin_amount,
                rec.fuel_sur_amount, rec.other_amount])
            return total

    def _get_computed_price_unit(self):
        # override this method for shipping service to set total (price_unit) base on shipping service lines amount.
        context = dict(self.env.context) or {}
        if context.get("is_service_quotation"):
            return self._get_custom_shipping_service_total()
        return super()._get_computed_price_unit()

    @api.onchange('freight_amount', 'insurance_amount', 'admin_amount', 'fuel_sur_amount', 'other_amount')
    def _onchange_service_quotation_amount(self):
        # Set total (price_unit) base on shipping service lines amount
        for rec in self:
            rec.price_unit = rec._get_custom_shipping_service_total()

    # FIXME: Disabled to prevent Infinite Recursion and Timeout during Invoice Confirmation.
    # @api.model_create_multi
    # def create(self, vals_list):
    #     # override this method to call onchange and set unit price.
    #     res = super().create(vals_list)
    #     for line in res:
    #         if line.move_id.move_type == 'out_invoice':
    #             line._onchange_product_uom_discount_price_unit()
    #     return res

    # def _get_computed_account(self):
    #     # override this method to set account base on journal default account.
    #     if self.move_id and self.move_id.journal_id and self.move_id.journal_id.default_account_id:
    #         return self.move_id.journal_id.default_account_id
    #     return super()._get_computed_account()


    def _compute_parent_id(self):
        """ Override: Avoid triggering recursion by only updating lines in self.
        The original method iterates all lines in the move and sets parent_id, which can trigger a write()
        on lines not currently in self, leading to re-computation loops if parent_id relates to stored fields or dependencies.
        """
        for move, lines in self.grouped('move_id').items():
            if not move:
                # If we have lines not seemingly attached to a move (new records?), handle them
                for line in lines:
                    line.parent_id = False
                continue

            last_section = False
            last_sub = False
            # Iterate all lines to correctly determine sections/subsections order
            for line in move.line_ids.sorted('sequence'):
                parent_id = False
                if line.display_type == 'line_section':
                    last_section = line
                    parent_id = False
                    last_sub = False
                elif line.display_type == 'line_subsection':
                    parent_id = last_section
                    last_sub = line
                elif line.display_type in {'line_note', 'product'}:
                    parent_id = last_sub or last_section
                else:
                    parent_id = False

                # FIX: Only assign to lines that are currently being computed (in self aka `lines`)
                # Checking `line in lines` works correctly for recordsets
                if line in lines:
                    line.parent_id = parent_id

    def action_view_shipping_line(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Shipping Line',
            'res_model': 'account.move.line',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': self.env.ref('panworld_account.shipping_lines_form_view').id,
            'target': 'new',
        }

    @api.constrains('account_id', 'display_type')
    def _check_payable_receivable(self):
        """Remove the validation for the partners which can be both Customer/Vendor.
        Check added based on the custom field allow_ar_ap"""
        for line in self:
            account_type = line.account_id.account_type
            if line.move_id.is_sale_document(include_receipts=True):
                if account_type == 'liability_payable':
                    raise UserError(
                        _("Account %s is of payable type, but is used in a sale operation.", line.account_id.code))
                if (line.display_type == 'payment_term') ^ (account_type == 'asset_receivable'):
                    raise UserError(_("Any journal item on a receivable account must have a due date and vice versa."))
            if line.move_id.is_purchase_document(include_receipts=True):
                if account_type == 'asset_receivable' and not line.partner_id.allow_ar_ap:
                    raise UserError(_("Account %s is of receivable type, but is used in a purchase operation.",
                                      line.account_id.code))
                if not line.partner_id.allow_ar_ap and (
                        (line.display_type == 'payment_term') ^ (account_type == 'liability_payable')):
                    raise UserError(_("Any journal item on a payable account must have a due date and vice versa."))

class ShippingTerm(models.Model):
    _name = 'shipping.term'
    _description = 'Shipping Term'

    name = fields.Char(
        string='Name', help='Name of shipping term', required="1")



