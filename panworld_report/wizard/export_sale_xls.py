# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
import io
import base64

from datetime import date

from datetime import datetime

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

from odoo.exceptions import UserError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class ExportSaleXls(models.TransientModel):
    _name = 'export.sale.xls'
    _description = 'Export Sale XLS'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)

    def action_export_excel(self):

        if self.start_date > self.end_date:
            raise UserError(_("Start Date must be less than End Date."))

        purchase_order_line = self.env['purchase.order.line']
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Shipping Tracking Report")
        sheet.set_column(0, 0, 25)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 25)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 30)
        sheet.set_column(5, 5, 22)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 25)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 20)
        sheet.set_column(11, 11, 15)
        sheet.set_column(12, 12, 18)
        sheet.set_column(13, 13, 15)
        sheet.set_column(14, 14, 10)
        sheet.set_column(15, 15, 10)
        sheet.set_column(16, 16, 10)
        sheet.set_column(17, 17, 10)
        sheet.set_column(18, 18, 20)
        sheet.set_column(19, 19, 33)
        sheet.set_column(20, 20, 25)
        sheet.set_column(21, 21, 40)
        sheet.set_column(22, 22, 20)
        sheet.set_column(23, 23, 20)
        sheet.set_column(24, 24, 25)
        format1 = workbook.add_format({'font_size': 10, 'align': 'center', 'border': 1})
        format_left = workbook.add_format({'font_size': 10, 'align': 'left'})
        format_right = workbook.add_format({'font_size': 10, 'align': 'right', 'border': 1})

        merge_format = workbook.add_format({
            'bold': 1, 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 11})

        merge_format_left = workbook.add_format({
            'bold': 1, 'border': 1, 'align': 'left', 'valign': 'vcenter', 'font_size': 10})

        text_color = workbook.add_format({'font_size': 10, 'align': 'center', 'border': 1, 'bold': True})
        text_color_left = workbook.add_format(
            {'font_size': 10, 'align': 'left', 'border': 1, 'bold': True, 'bg_color': '#FFFF00'})
        text_color_right = workbook.add_format({'font_size': 10, 'align': 'right', 'border': 1, 'bold': True})

        r, c = 0, 0

        sheet.write(r, c, 'Customer Sales Order', text_color_left)
        c += 1
        sheet.write(r, c, 'Sales Order Date', text_color_left)
        c += 1
        sheet.write(r, c, 'Odoo Sales Order Number', text_color_left)
        c += 1
        sheet.write(r, c, 'ISBN', text_color_left)
        c += 1
        sheet.write(r, c, 'Title Name', text_color_left)
        c += 1
        sheet.write(r, c, 'Sales Order Quantity', text_color_left)
        c += 1
        sheet.write(r, c, 'Purchase Order', text_color_left)
        c += 1
        sheet.write(r, c, 'Purchase Order Date', text_color_left)
        c += 1
        sheet.write(r, c, 'Vendor Name', text_color_left)
        c += 1
        sheet.write(r, c, 'Purchase Placed Qty', text_color_left)
        c += 1
        sheet.write(r, c, 'Billed Quantity', text_color_left)
        c += 1
        sheet.write(r, c, 'Reorder/Pending Qty', text_color_left)
        c += 1
        sheet.write(r, c, 'Supplier Bill Number', text_color_left)
        c += 1
        sheet.write(r, c, 'Supplier Bill Date', text_color_left)
        c += 1
        sheet.write(r, c, 'Currency', text_color_left)
        c += 1
        sheet.write(r, c, 'List Price', text_color_left)
        c += 1
        sheet.write(r, c, 'Discount', text_color_left)
        c += 1
        sheet.write(r, c, 'Net Price', text_color_left)
        c += 1
        sheet.write(r, c, 'Total Value', text_color_left)
        c += 1
        sheet.write(r, c, 'Vendor to Shipper Wh tracking Number', text_color_left)
        c += 1
        sheet.write(r, c, 'Delivery Date at Shipper Location', text_color_left)
        c += 1
        sheet.write(r, c, 'Shipper to Our WH moving date', text_color_left)
        c += 1
        sheet.write(r, c, 'Shipper to Our Wh Tracking Number', text_color_left)
        c += 1
        sheet.write(r, c, 'Our Wh Received Date', text_color_left)
        c += 1
        sheet.write(r, c, 'Our Wh received Qty', text_color_left)
        c += 1
        sheet.write(r, c, 'REMARK', text_color_left)

        r += 1

        SaleOrder = self.env['sale.order']

        domain = [
            ('date_order', '>=', self.start_date),
            ('date_order', '<=', self.end_date)
        ]
        orders = SaleOrder.search(domain, order="date_order desc")

        for order in orders:
            for order_line in order.order_line:
                for move in order_line.move_ids:
                    c = 0
                    sheet.write(r, c, order.customer_sales_order or '', format_left)
                    c += 1
                    date_order = fields.Datetime.to_string(order.date_order) if order.date_order else ''
                    sheet.write(r, c, date_order or '', format_left)
                    c += 1
                    sheet.write(r, c, order.name or '', format_left)
                    c += 1
                    sheet.write(r, c, order_line.product_id.barcode or '', format_left)
                    c += 1
                    sheet.write(r, c, order_line.product_id.name or '', format_left)
                    c += 1
                    sheet.write(r, c, order_line.product_uom_qty or '', format_left)

                    purchase_line = purchase_order_line.search([('sale_line_id', 'in', [order_line.id])])
                    if not purchase_line:
                        purchase_line = purchase_order_line.search(
                            [('move_dest_ids.group_id.sale_id', 'in', [order.id])]) or \
                                        purchase_order_line.search(
                                            [('move_ids.move_dest_ids.group_id.sale_id', 'in', [order.id])])

                    if purchase_line:
                        c += 1
                        sheet.write(r, c, purchase_line.order_id.name or '', format_left)
                        c += 1
                        date_order = fields.Datetime.to_string(
                            purchase_line.order_id.date_order) if purchase_line.order_id.date_order else ''
                        sheet.write(r, c, date_order or '', format_left)
                        c += 1
                        sheet.write(r, c, purchase_line.order_id.partner_id.name or '', format_left)
                        c += 1
                        sheet.write(r, c, purchase_line.product_qty or '', format_left)
                        c += 1
                        sheet.write(r, c, purchase_line.qty_invoiced or '', format_left)
                        c += 1
                        sheet.write(r, c, float(purchase_line.product_qty - purchase_line.qty_received) or '',
                                    format_left)
                        c += 1
                        sheet.write(r, c, purchase_line.invoice_lines.move_name or '', format_left)
                        c += 1
                        invoice_date = fields.Datetime.to_string(
                            purchase_line.invoice_lines.move_id.invoice_date) if purchase_line.invoice_lines.move_id.invoice_date else ''
                        sheet.write(r, c, invoice_date or '', format_left)
                        c += 1
                        sheet.write(r, c, purchase_line.currency_id.name or '', format_left)
                        c += 1
                        sheet.write(r, c, purchase_line.price_unit or '', format_left)
                        c += 1
                        sheet.write(r, c, purchase_line.discount or '', format_left)
                        c += 1
                        sheet.write(r, c, purchase_line.list_price or '', format_left)
                        c += 1
                        sheet.write(r, c, purchase_line.price_subtotal or '', format_left)
                        c += 1
                        stock_picking = self.env['stock.picking'].search(
                            [('id', 'in', purchase_line.order_id.picking_ids.ids)])
                        carrier_tracking_ref = ''
                        shp_wh_dispatch_date = ''
                        wh_carrier_tracking_ref = ''
                        date_done = ''
                        scheduled_date = ''
                        quantity_done = 0
                        remarks = ''
                        for pick in stock_picking:
                            if pick.picking_type_id.code == 'internal':
                                carrier_tracking_ref = pick.carrier_tracking_ref
                                if pick.shp_wh_dispatch_date:
                                    shp_wh_dispatch_date = fields.Datetime.to_string(pick.shp_wh_dispatch_date)
                            if pick.picking_type_id.code == 'incoming':
                                wh_carrier_tracking_ref = pick.carrier_tracking_ref
                                total_done = pick.total_done
                                if pick.scheduled_date:
                                    scheduled_date = fields.Datetime.to_string(pick.scheduled_date)
                                if pick.date_done:
                                    date_done = fields.Datetime.to_string(pick.date_done)

                        sheet.write(r, c, carrier_tracking_ref, format_left)
                        c += 1
                        sheet.write(r, c, shp_wh_dispatch_date, format_left)

                        c += 1
                        sheet.write(r, c, scheduled_date, format_left)
                        c += 1
                        sheet.write(r, c, wh_carrier_tracking_ref, format_left)
                        c += 1
                        sheet.write(r, c, date_done, format_left)
                        c += 1
                        sheet.write(r, c, purchase_line.qty_received, format_left)
                        c += 1
                        sheet.write(r, c, '', format_left)

                    r += 1

        workbook.close()
        output.seek(0)
        data = base64.b64encode(output.getvalue())
        output.close()

        attch_obj = self.env['ir.attachment']
        attach_ids = attch_obj.search([
            ('res_model', '=', 'export.sale.xls')])
        if attach_ids:
            try:
                attach_ids.unlink()
            except:
                pass

        doc_id = attch_obj.create({
            'name': '%s.xls' % ('Sale Order'),
            'datas': data,
            'res_model': 'export.sale.xls'
        })
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/%s?download=true' % (doc_id.id),
            'target': 'current',
            'tag': 'close',
        }
