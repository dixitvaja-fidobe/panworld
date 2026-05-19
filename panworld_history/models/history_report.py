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


class ResHistory(models.TransientModel):
    _name = "res.history.report"

    name = fields.Char()

class HistoryReport(models.TransientModel):
    _name = 'history.report'
    _description = 'History Report'

    #sale order
    date_order = fields.Datetime('Order Date')
    order_reference = fields.Char('Order Reference')
    sale_order_id = fields.Many2one('sale.order',string='Related Sale Order')
    partner_id = fields.Many2one('res.partner','Customer')
    barcode = fields.Char('ISBN')
    division_type_id = fields.Many2one('division.type','Division Type')
    description = fields.Char('Description')
    currency_id = fields.Many2one('res.currency','Currency')
    price_unit = fields.Float('List Price')
    discount = fields.Float('Discount %')
    list_price = fields.Float('Unit Price')
    so_quantity = fields.Float('Product Qty')
    qty_delivered = fields.Float('Delivered Quantity')
    qty_invoiced = fields.Float('Invoiced Quantity')
    price_subtotal = fields.Monetary(string="Subtotal",
        currency_field="currency_id")
    company_id = fields.Many2one('res.company', string="Company")
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status')
    report_id = fields.Many2one('res.history.report')

    #invoice
    invoice_date = fields.Date('Invoice date')
    invoice_number = fields.Char('Invoice number')
    delivery_note = fields.Char('Delivery Note')
    cso_reference = fields.Char('CSO Reference')
    vat_amount = fields.Monetary(string="Vat",
                                     currency_field="currency_id")
    invoice_state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], string='Status')
    quantity = fields.Float('Invoice Quantity')
    invoice_id = fields.Many2one('account.move', string='Related Invoice')
    product_weight = fields.Float('Product Weight')
    tracking_number = fields.Many2one('tracking.number', string='Tracking Number')
    ship_number = fields.Char('Ship No.',related="invoice_id.ship_reference")
    his_total_ship_kgs = fields.Float('Total Shipping Charges- Per Kgs',related="invoice_id.total_ship_kgs")
    his_cons_weight = fields.Float('Consolidated Weight',related="invoice_id.cons_weight")
    bill_ref = fields.Char('Bill Reference',related="invoice_id.ref")
    carrier_tracking = fields.Many2one('delivery.carrier', string="Delivery Method", related="invoice_id.carrier_id")



    #purchase
    purchase_order_id = fields.Many2one('purchase.order', string='Related Purchase Order')
    customer_name = fields.Char('Customer Name')
    customer_order_number = fields.Char('Customer Order Number')
    customer_sales_order = fields.Char('Customer Sales Order')
    po_list_price = fields.Float('PO List Price')
    po_discount = fields.Float('PO Discount %')
    po_price = fields.Float('PO Unit Price')
    po_qty = fields.Float('PO Quantity')
    qty_received = fields.Float('Received Qty')
    po_state = fields.Selection([
        ('draft', 'Draft RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], 'Status')

    #credit note
    rma_id = fields.Many2one('rma.ret.mer.auth',string='RMA')

    #bill
    po_ref = fields.Char(string='PO Reference', compute='get_ref')

    @api.depends('invoice_id','invoice_id.po_ref_ids')
    def get_ref(self):
        """get multi po ref for one invoice/Bill"""
        for rec in self:
            rec.po_ref = ', '.join(rec.invoice_id.po_ref_ids.mapped('name'))

    # delivery Note
    scheduled_date = fields.Datetime('Date')
    delivery_reference = fields.Char('Reference')
    delivery_note_id = fields.Many2one('stock.picking','Related Delivery Note')
    carrier_tracking_ref = fields.Char('Tracking')
    location_id = fields.Many2one('stock.location','From location')
    picking_state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status')


    #Vendor Credit
    bill_reference = fields.Char('Bill Reference')

    #grn
    customer_sales_order = fields.Char('Customer Sales Order')
    customer_name = fields.Char('Customer Name')
    landed_cost = fields.Float('Landed Cost/ Per unit',compute='get_landed_cost')
    landed_cost_line_id = fields.Many2one(string="Acquirer", comodel_name='landed.cost.valuation.lines')
    grn_tracking_number_id = fields.Many2one("tracking.number", string='Tracking Number')

    # @api.depends('landed_cost_line_id')
    # def get_landed_cost(self):
    #     for rec in self:
    #         landed_cost = 0
    #         if rec.landed_cost_line_id and getattr(rec.landed_cost_line_id, 'cost_id',False):
    #             landed_cost = rec.landed_cost_line_id.former_cost
    #             lines = rec.landed_cost_line_id.cost_id.landed_cost_valuation_lines.filtered(lambda x:x.product_id.id == rec.landed_cost_line_id.product_id.id)
    #             if lines:
    #                 additional_landed_cost = sum(lines.mapped('additional_landed_cost'))/len(lines)
    #                 former_cost = sum(lines.mapped('former_cost'))/len(lines)
    #                 # landed_cost += sum(lines.mapped('additional_landed_cost'))/len(lines)
    #                 cost = additional_landed_cost / len(lines.mapped('quantity'))
    #                 landed_cost = former_cost + cost
    #         rec.landed_cost = landed_cost

    # @api.depends('landed_cost_line_id')
    def get_landed_cost(self):
        for rec in self:
            landed_cost = 0
            if rec.landed_cost_line_id and getattr(rec.landed_cost_line_id, 'cost_id', False):
                landed_cost = rec.landed_cost_line_id.former_cost
                lines = rec.landed_cost_line_id.cost_id.landed_cost_valuation_lines.filtered(
                    lambda x: x.product_id.id == rec.landed_cost_line_id.product_id.id)
                if lines:
                    try:
                        landed_cost = (landed_cost + (rec.landed_cost_line_id.additional_landed_cost / sum(lines.mapped(
                            'quantity')) * rec.landed_cost_line_id.quantity)) / rec.landed_cost_line_id.quantity
                    except:
                        landed_cost = 0
            rec.landed_cost = landed_cost

    #Inventory Adjustment
    date = fields.Datetime('Date')
    reference = fields.Char('Reference')
    location_dest_id = fields.Many2one('stock.location', 'To location')
    cost = fields.Float('Cost', compute="_get_cost_price")
    stock_move_line_state = fields.Selection([
        ('draft', 'New'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Move'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Available'),
        ('done', 'Done')], string='Status',)
    product_id = fields.Many2one('product.product')
    value_adjustment = fields.Float('Value Adjustment',compute="_get_cost_price")

    @api.depends('product_id', 'quantity', 'product_id.standard_price')
    def _get_cost_price(self):
        """Get Cost Price and Value Adjustment"""
        for rec in self:
            rec.cost = rec.product_id.standard_price
            rec.value_adjustment = (rec.product_id.standard_price * rec.quantity)
