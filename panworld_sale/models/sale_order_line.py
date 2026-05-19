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
from collections import defaultdict
# from odoo.exceptions import Warning, AccessDenied,UserError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    weight = fields.Float(
        related="product_id.weight", string="Weight (in g)", help="Product weight"
    )
    total_weight = fields.Float(
        compute="_compute_total_weight",
        string="Total Weight (in g)",
        help="Total product weight base on product quantity", store=True
    )
    list_price = fields.Float(
        string="List Price", digits="Product Price", help="Unit price (after discount)"
    )
    remarks = fields.Char(string="Remarks")
    # landed_cost = fields.Float(
    #     compute="_compute_landed_cost", string="LCO", help="Landed cost"
    # )
    landed_cost = fields.Float(compute="_compute_total_weight", string="LCO", help="Landed cost", store=True)
    marketplace_cost = fields.Float(
        compute="_compute_marketplace_cost",
        string="MCO",
        help="Marketplace cost base on configuration in customer",
        store=True,
    )
    shipping_cost = fields.Float(
        compute="_compute_shipping_cost",
        string="SCO",
        help="Shipping cost base on product total weight",
        store=True,
    )
    other_cost = fields.Float(
        compute="_compute_other_cost",
        string="OCO",
        help="Other cost base on configuration in customer",
        store=True,
    )
    subtotal_cost = fields.Float(
        compute="_compute_subtotal_cost",
        string="TCO (Subtotal)",
        help="Subtotal cost base on SCO, MCO, OCO and LCO", store=True
    )
    gp_percentage = fields.Float(
        compute="_compute_gp_percentage",
        string="GP%",
        help="GP percentage base on subtotal and TCO subtotal", store=True
    )
    barcode = fields.Char(related='product_id.barcode', string='ISBN')
    uk_wholesaler_id = fields.Many2one(comodel_name="product.grade", string='Grade')
    invoice_ref = fields.Char(compute="_compute_invoice_ref_date", string='Invoice Reference/Invoice Date')
    course_id = fields.Char(string='Course ID', help='Course ID for Sharjah University')
    crn = fields.Char(string='CRN', help='CRN for Sharjah University')
    lock_price_disc = fields.Boolean("Lock Price & Discount", default=True)
    subject_id = fields.Many2one(comodel_name="product.subject", string='Subject')
    format = fields.Char(string='Format')
    classification = fields.Char(string='Classification')
    available_qty_stock = fields.Float(related='product_id.free_qty', string='Available Qty in Stock', readonly=True)

    @api.depends('product_id', 'order_id.fiscal_position_id', 'company_id')
    def _compute_tax_ids(self):
        """Override the compute method to set the default sales tax for SO lines"""
        # Group lines by company for efficiency
        lines_by_company = defaultdict(lambda: self.env['sale.order.line'])
        for line in self:
            lines_by_company[line.company_id] += line
        for company, lines in lines_by_company.items():
            for line in lines.with_company(company):
                taxes = self.env['account.tax']
                if line.product_id:
                    # Filter product taxes by company
                    taxes = line.product_id.taxes_id.filtered(lambda t: t.company_id == company or not t.company_id)
                
                fiscal_position = line.order_id.fiscal_position_id
                if fiscal_position:
                    result = fiscal_position.map_tax(taxes)
                else:
                    result = taxes
                
                # FALLBACK: If no taxes found or mapped, use company default tax
                if not result and company.account_sale_tax_id:
                    result = company.account_sale_tax_id
                
                # CLEANUP: If multiple taxes are returned (e.g. due to overlapping Fiscal Position rules),
                # and the Company's Default Tax is one of them, prioritize the default tax.
                if len(result) > 1 and company.account_sale_tax_id and company.account_sale_tax_id in result:
                    result = company.account_sale_tax_id
                
                # Final safeguard for company filtering
                if result:
                    result = result.filtered(lambda t: t.company_id == company or not t.company_id)
                
                line.tax_ids = result

    @api.depends("product_id", "product_uom_qty")
    def _compute_total_weight(self):
        # Get total weight of product base on (product weight and qty).
        for rec in self:
            rec.total_weight = rec.product_id.weight * rec.product_uom_qty
            rec.landed_cost = rec.product_id.standard_price * rec.product_uom_qty

    @api.depends("order_id.partner_id", "price_subtotal", "order_id.customer_so_date")
    def _compute_marketplace_cost(self):
        # Get MCO base on (marketplace cost (conf in customer) and subtotal).
        for rec in self:
            if rec.order_id.customer_so_date and rec.order_id.partner_id:
                rec.marketplace_cost = (
                    rec.price_subtotal
                    * rec.order_id.partner_id._get_marketplace_other_cost(
                        date_order=rec.order_id.customer_so_date
                    ).get("marketplace_cost")
                    / 100.0
                )

    @api.depends("order_id.partner_id", "price_subtotal", "order_id.customer_so_date")
    def _compute_other_cost(self):
        # Get OCO base on (other cost (conf in customer) and subtotal).
        for rec in self:
            if rec.order_id.customer_so_date and rec.order_id.partner_id:
                rec.other_cost = (
                    rec.price_subtotal
                    * rec.order_id.partner_id._get_marketplace_other_cost(
                        date_order=rec.order_id.customer_so_date
                    ).get("other_cost")
                    / 100.0
                )

    @api.depends("shipping_cost", "marketplace_cost", "other_cost", "landed_cost")
    def _compute_subtotal_cost(self):
        # Get TCO (Subtotal) base on (SCO, MCO, OCO and LCO).
        for rec in self:
            rec.subtotal_cost = (
                rec.shipping_cost
                + rec.marketplace_cost
                + rec.other_cost
                + rec.landed_cost
            )

    @api.depends("price_subtotal", "subtotal_cost")
    def _compute_gp_percentage(self):
        # Get GP% base on (subtotal and TCO subtotal).
        gp_percentage = 0.0
        for rec in self:
            if rec.price_subtotal > 0:
                gp_percentage = (
                    (rec.price_subtotal - rec.subtotal_cost)
                    / rec.price_subtotal
                    * 100.0
                )
            rec.gp_percentage = gp_percentage

    @api.depends("order_id.pw_shipping_cost")
    def _compute_shipping_cost(self):
        # Get shipping cost base on delivery method and total weight).
        shipping_cost = 0.0
        for rec in self:
            if (
                rec.order_id.total_weight > 0
                and rec.order_id.pick_type == "door_delivery"
            ):
                shipping_cost = (
                        rec.order_id.pw_shipping_cost / rec.order_id.total_weight
                    ) * rec.total_weight
            rec.shipping_cost = shipping_cost

    # @api.depends("product_uom_qty", "product_id")
    # def _compute_landed_cost(self):
    #     # Get landed cost.
    #     for rec in self:
    #         rec.landed_cost = rec.product_id.standard_price * rec.product_uom_qty

    def _compute_invoice_ref_date(self):
        for rec in self:
            rec.invoice_ref = ''
            coma = False
            if len(rec.order_id.invoice_ids) > 1:
                coma = True
            for inv in rec.order_id.invoice_ids:
                # inv_name = "inv.display_name"
                if inv.invoice_date:
                    inv_date = inv.invoice_date
                else:
                    inv_date = inv.date
                if coma:
                    rec.invoice_ref += inv.display_name + " : " + fields.Date.to_string(inv_date) + ' , '
                else:
                     rec.invoice_ref = inv.display_name + " : " + fields.Date.to_string(inv_date)

    @api.onchange('product_uom_id', 'product_uom_qty')
    def product_uom_change(self):
        # Customization
        # Override base method to add one condition for preventing price updation in sale order
        # If "lock_price_disc" boolean is True
        if not self.product_uom_id or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom_id.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            if not self.lock_price_disc:  # Custom condition to prevent updation of price on changing quantities
                self.price_unit = product._get_tax_included_unit_price(
                    self.company_id or self.order_id.company_id,
                    self.order_id.currency_id,
                    self.order_id.date_order,
                    'sale',
                    fiscal_position=self.order_id.fiscal_position_id,
                    product_price_unit=self._get_display_price(product),
                    product_currency=self.order_id.currency_id
                )

    @api.onchange('product_id', 'price_unit', 'product_uom_id', 'product_uom_qty', 'tax_ids')
    def _onchange_discount(self):
        if not (self.product_id and self.product_uom_id and
                self.order_id.partner_id and self.order_id.pricelist_id and
                self.env.user.has_group('product.group_discount_per_so_line')):
            return

        if not self.lock_price_disc:  # Customization condition...to prevent updation of discount on changing quantities
            self.discount = 0.0

        product = self.product_id.with_context(
            lang=self.order_id.partner_id.lang,
            partner=self.order_id.partner_id,
            quantity=self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom_id.id,
            fiscal_position=self.env.context.get('fiscal_position')
        )

        product_context = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order, uom=self.product_uom_id.id)

        price, rule_id = self.order_id.pricelist_id.with_context(product_context).get_product_price_rule(self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
        new_list_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id, self.product_uom_qty, self.product_uom_id, self.order_id.pricelist_id.id)

        if new_list_price != 0:
            if self.order_id.pricelist_id.currency_id != currency:
                # we need new_list_price in the same currency as price, which is in the SO's pricelist's currency
                new_list_price = currency._convert(
                    new_list_price, self.order_id.pricelist_id.currency_id,
                    self.order_id.company_id or self.env.company, self.order_id.date_order or fields.Date.today())
            discount = (new_list_price - price) / new_list_price * 100
            if (discount > 0 and new_list_price > 0) or (discount < 0 and new_list_price < 0):
                if not self.lock_price_disc:  # Customization condition
                    self.discount = discount

    @api.onchange("product_uom_id", "product_uom_qty", "discount", "price_unit")
    def _onchange_uom_qty_discount_price_unit(self):
        # Get unit price base on list price and discount
        for rec in self:
            list_price = rec.price_unit
            if rec.discount:
                list_price = rec.price_unit - (rec.price_unit * rec.discount / 100.0)
            rec.list_price = list_price

    def _prepare_invoice_line(self, **optional_values):
        # pass panworld custom fields values in customer invoice.
        vals = super()._prepare_invoice_line(**optional_values)
        vals.update({
            'course_id': self.course_id or '',
            'crn': self.crn or ''
        })
        return vals
