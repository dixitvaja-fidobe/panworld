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
from odoo.tools import drop_view_if_exists
import re
import datetime


class SaleTracker(models.Model):
    _name = 'sales.tracker.report'
    _description = 'SaleTracker'
    _auto = False
    _check_company_auto = True

    sale_tat = fields.Char(string="Sale TAT", compute="_get_sale_tat")

    so_date = fields.Date(string="SO Date")
    so_id = fields.Many2one('sale.order', string="SO Number")
    cus_id = fields.Many2one('res.partner', string="Customer Name")
    div_type_id = fields.Many2one('division.type', string="Customer Type")
    so_no = fields.Char(string="SO Ref")
    customer_account = fields.Char('Customer Account')

    sol_id = fields.Many2one('sale.order.line', string="Sale order line")
    sales_price = fields.Float('Sales Price AED')
    so_confirm_qty = fields.Float('SO Confirm Qty')
    so_cancel_qty = fields.Float('SO Cancel Qty')
    so_cancellation_reason = fields.Char('SO Cancellation Reason')
    product_barcode = fields.Char(string="ISBN")
    product_id = fields.Many2one('product.product', string="Product Name")
    product_name = fields.Char(string="Product Name", compute="_get_product_name")  # change in _search meth.
    asin = fields.Date('ASIN')
    sale_price = fields.Float(string="Sales Price")
    so_qty = fields.Float(string="SO Qty")
    pending_so_qty = fields.Float("Pending SO Qty", compute='_compute_pending_so_qty')
    pending_customer_invoice_qty = fields.Float('Pending Cust_Invocie Qty')
    inv_qty = fields.Float(string="Customer Invoice Qty")
    company_id = fields.Many2one('res.company', string="Company")

    wh1_stock = fields.Float(string="Panworld General Trading LLC", compute="_get_warehouse_qty")
    wh2_stock = fields.Float(string="UK 3PL Warehouse", compute="_get_warehouse_qty")
    wh3_stock = fields.Float(string="Croissance R Holding FZ-LLC", compute="_get_warehouse_qty")
    wh4_stock = fields.Float(string="Panworld Education FZC", compute="_get_warehouse_qty")
    wh5_stock = fields.Float(string="Pinnacle Educational Supplies LLC", compute="_get_warehouse_qty")
    wh6_stock = fields.Float(string="Book Panworld Publishing & Distribution Company", compute="_get_warehouse_qty")

    stock_status = fields.Char("Stock Status", compute='_compute_pending_so_qty')

    po_id = fields.Many2one('purchase.order', string="PO Number")
    vendor_id = fields.Many2one('res.partner', string="Vendor Name")
    vendor_type_id = fields.Many2one('division.type', string="Vendor Type")
    publisher_id = fields.Many2one('res.partner', string="Publisher")
    invoiced_qty = fields.Float('Invoice Qty')
    pol_id = fields.Many2one('purchase.order.line', string="Purchase order line")
    po_target_price = fields.Float(string="PO Target Price")
    pol_po_qty = fields.Float('PO Quantity')
    po_back_order_qty = fields.Float('PO Back Order Qty', compute="compute_po_backorder_qty")
    po_cancelled_qty = fields.Float('Cancelled PO Qty', compute="compute_po_backorder_qty")
    po_pending_qty = fields.Float('Pending PO Qty')
    po_currency_id = fields.Many2one('res.currency', 'Currency - PO')
    bill_list_price = fields.Float('Bill List Price')
    bill_dis = fields.Float('Bill. Disc')
    bill_unit_price = fields.Float('Bill Unit Price')
    bill_unit_price_currency = fields.Float('Bill Unit Price- AED')
    carrier_id = fields.Many2one('delivery.carrier', 'Shipper')
    processed_qty = fields.Float('Processed Qty')
    non_processed_qty = fields.Float('Non-Processed Qty')
    mat_received_qty = fields.Float('Mat_Received Qty-WH')

    grn_picking_id = fields.Many2one('stock.picking', 'GRN No.', compute='_get_grn_no')
    mat_received_date = fields.Datetime(string='Mat_Received Date-WH', compute='_get_grn_no')

    def _get_sale_tat(self):
        ship_picking_type_ids = self.env['stock.picking.type'].sudo().search([('sequence_code', '=', 'OUT')]).ids
        for rec in self:
            if rec.so_id:
                today = datetime.datetime.today().date()
                so_picking = self.env['stock.picking'].search(
                    [('picking_type_id', 'in', ship_picking_type_ids), ('sale_id', '=', rec.so_id.id)], order='create_date asc', limit=1)
                if so_picking and rec.so_id.commitment_date and so_picking.scheduled_date.date() > rec.so_id.commitment_date.date():
                    rec.sale_tat = 'TAT Breached'
                    rec.so_id.tat_breach = True
                elif so_picking and rec.so_id.commitment_date and ((today - rec.so_id.commitment_date.date()).days) > rec.div_type_id.sale_tat:
                    rec.sale_tat = 'Cancelation Risk'
                elif so_picking and rec.so_id.commitment_date and ((today - rec.so_id.commitment_date.date()).days) <= rec.div_type_id.sale_tat:
                    rec.sale_tat = 'On Time'
                else:
                    rec.sale_tat = None


    def _get_warehouse_qty(self):
        for rec in self:
            warehouse_map = {
                'wh_pw_general': 'wh1_stock',
                'wh_uk_3pl': 'wh2_stock',
                'wh_croissance': 'wh3_stock',
                'wh_pw_education': 'wh4_stock',
                'wh_pinnacle_education': 'wh5_stock',
                'bppadc': 'wh6_stock'
            }
            for wh in self.env['stock.warehouse'].search([]):
                stock = 0.0
                if warehouse_map.get(wh.sale_tracker_report_code, False):
                    stock = rec.product_id.with_context(warehouse=wh.id).qty_available
                setattr(rec, warehouse_map.get(wh.sale_tracker_report_code), stock)

    def compute_po_backorder_qty(self):
        for rec in self:
            move = rec.pol_id.move_ids.filtered(lambda l: l.purchase_line_id.id == rec.pol_id.id)
            if move.filtered(lambda l: l.state == 'cancel'):
                cancel_move = move.filtered(lambda l: l.state == 'cancel').mapped('product_uom_qty')
            else:
                cancel_move = move.move_orig_ids.filtered(lambda l: l.state == 'cancel').mapped('product_uom_qty')
            rec.po_cancelled_qty = sum(cancel_move) + rec.pol_id.cancel_qty if cancel_move else rec.pol_id.cancel_qty
            rec.po_back_order_qty = rec.pol_id.product_qty - rec.pol_id.qty_received if rec.pol_id.order_id.picking_ids.mapped(
                'backorder_id') and not rec.pol_id.move_ids.filtered(lambda l: l.state == 'cancel') else 0

    def _get_product_name(self):
        for rec in self:
            if rec.sol_id.name:
                pattern = re.compile(r'\[.*?\]')
                result = re.sub(pattern, '', rec.sol_id.name)
                rec.product_name = result
            else:
                rec.product_name = None

    def _get_grn_no(self):
        for rec in self:
            if rec.po_id and rec.po_id.picking_type_id.code == 'incoming' and rec.po_id.picking_type_id.default_location_dest_id.usage != 'transit' and not rec.po_id.picking_type_id.default_location_dest_id.is_shipper_location:
                rec.grn_picking_id = self.env['stock.picking'].sudo().search([('id', 'in', rec.po_id.picking_ids.ids), ('state', '=', 'done')],
                                                                             order='create_date desc', limit=1).id
                rec.mat_received_date = self.env['stock.picking'].sudo().search(
                    [('id', 'in', rec.po_id.picking_ids.ids), ('state', '=', 'done')],
                    order='create_date desc',
                    limit=1).scheduled_date
            else:
                rec.grn_picking_id = None
                rec.mat_received_date = None

    def _compute_pending_so_qty(self):
        for rec in self:
            ttl_wh_qty = sum(
                [getattr(rec, x, 0.0) for x in self.env.company.mapped('sale_tracker_warehouse_fields.name')])
            pending_so_qty = rec.so_qty - ttl_wh_qty
            rec.pending_so_qty = pending_so_qty
            rec.stock_status = pending_so_qty < 1 and 'In Stock' or 'Purchase'

    def _query(self):
        return f"""
            select
            *,
            row_number() OVER(ORDER BY sol_pol_data.so_id ASC) as id,
            (sol_pol_data.so_confirm_qty - sol_pol_data.processed_qty) as non_processed_qty
            from(
                select
                    sol_data.so_id as so_id,
                    sol_data.sol_id as sol_id,
                    sol_data.so_company_id as company_id,
                    sol_data.so_qty as so_qty,
                    sol_data.inv_qty as inv_qty,
                    sol_data.so_date as so_date,
                    sol_data.div_type_id as div_type_id,
                    sol_data.customer_account as customer_account,
                    sol_data.sales_price as sales_price,
                    sol_data.so_cancel_qty as so_cancel_qty,
                    sol_data.so_confirm_qty as so_confirm_qty,
                    sol_data.product_barcode as product_barcode,
                    sol_data.asin as asin,
                    sol_data.so_name as so_no,
                    sol_data.partner_id as cus_id,
                    sol_data.so_cancellation_reason as so_cancellation_reason,
                    sol_data.sale_price as sale_price,
                    sol_data.product_id as product_id,
                    sol_data.pending_customer_invoice_qty as pending_customer_invoice_qty,
                    pol_data.po_id as po_id,
                    pol_data.pol_id as pol_id,
                    pol_data.vendor_id as vendor_id,
                    pol_data.vendor_type_id as vendor_type_id,
                    pol_data.publisher_id as publisher_id,
                    pol_data.po_target_price as po_target_price,
                    pol_data.pol_po_qty as pol_po_qty,
                    pol_data.po_pending_qty as po_pending_qty,
                    pol_data.po_currency_id as po_currency_id, 
                    pol_data.bill_list_price as bill_list_price,
                    pol_data.bill_dis as bill_dis,
                    pol_data.bill_unit_price as bill_unit_price,
                    pol_data.bill_unit_price_currency as bill_unit_price_currency,
                    pol_data.carrier_id as carrier_id,
                    pol_data.invoiced_qty as invoiced_qty,
                    pol_data.processed_qty as processed_qty,
                    pol_data.mat_received_qty as mat_received_qty
                from(
                    select
                        sol.id as sol_id,
                        sol.product_id as sol_product_id,
                        so.company_id as so_company_id,
                        so.currency_rate * sol.list_price as sales_price,
                        sol.list_price as sale_price,
                        so.division_type_id as div_type_id,
                        so.customer_account as customer_account,
                        sol.product_id as product_id,
                        sol.so_quantity - sol.cancelled_qty as so_confirm_qty,
                        sol.so_quantity  as so_qty,
                        sol.cancelled_qty as so_cancel_qty,
                        sol.qty_invoiced as inv_qty,
                        sol.cancel_reason as so_cancellation_reason,
                        sol.qty_delivered - sol.qty_invoiced as pending_customer_invoice_qty,
                        so.id as so_id,
                        so.partner_id as partner_id,
                        so.date_order as so_date,
                        so.name as so_name,
                        pp.barcode as product_barcode,
                        pp.publication_date as asin
                    from sale_order_line sol
                    JOIN sale_order so ON so.id = sol.order_id
                    JOIN product_product pp ON pp.id = sol.product_id 
                    where so.state in ('sale', 'done')) sol_data
                LEFT JOIN (
                    select
                        po.id as po_id,
                        pol.id as pol_id,
                        po.company_id as po_company_id,
                        pol.sale_reference,
                        po.currency_id as po_currency_id,
                        pol.partner_id as vendor_id,
                        pol.list_price as bill_list_price,
                        pol.price_unit as bill_unit_price,
                        pol.list_price * po.currency_rate as bill_unit_price_currency,
                        pol.discount as bill_dis,
                        pol.po_target_price as po_target_price,
                        rp.division_type_id as vendor_type_id,
                        po.publisher_id as publisher_id,
                        pol.product_id as pol_product_id,
                        pol.po_qty as pol_po_qty,
                        pol.po_qty - pol.qty_received as po_pending_qty,
                        pol.qty_received as mat_received_qty,
                        po.currency_id,
                        po.carrier_id,
                        pol.qty_invoiced as invoiced_qty,
                        pol.qty_invoiced as processed_qty
                    from purchase_order_line pol
                    JOIN purchase_order po ON po.id = pol.order_id
                    JOIN res_partner rp ON rp.id = po.partner_id
                    JOIN sale_order so ON so.name = pol.sale_reference
                    where pol.sale_reference != '' and po.state in ('purchase', 'done')
                    order by po.id) pol_data
                ON pol_data.sale_reference = sol_data.so_name
                   AND pol_data.po_company_id = sol_data.so_company_id
                   AND pol_data.pol_product_id = sol_data.sol_product_id
            ) sol_pol_data"""

    def init(self):
        drop_view_if_exists(self.env.cr, self._table)
        self._cr.execute(
            """CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))
