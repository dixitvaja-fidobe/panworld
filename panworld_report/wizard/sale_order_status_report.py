# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
import xlsxwriter
from odoo.exceptions import UserError
from odoo import models, fields, api, exceptions, _
import base64
import binascii
import logging
import os
import tempfile
import calendar
from datetime import date, timedelta


class SaleOrderStatusReport(models.TransientModel):
    _name = 'sale.order.status.report'
    _description = 'Sale Order status report'

    # start_date = fields.Date(string='Start Date', default=fields.Date.today(), required=True)
    start_date = fields.Date(string='Start Date', default=fields.Date.today().replace(day=1), required=True)
    end_date = fields.Date(string='End Date', default=fields.Date.today().replace(
        day=calendar.monthrange(date.today().year, date.today().month)[1]), required=True)
    # end_date = fields.Date(string='End Date', default=fields.Date.today(), required=True)
    so_ids = fields.Many2many('sale.order', string="Sale Order")
    so_tracking_ids = fields.Many2many('sale.order', "sale_order_tracker_rel", string="Sale Order")
    partner_ids = fields.Many2many('res.partner', string="Customer")
    division_ids = fields.Many2many('division.type', string="Division")
    so_status = fields.Selection([("closed", "Closed"), ("open", "Open")],
                                 string="SO Status")

    @api.onchange('start_date', 'end_date')
    def onchange_start_end_date(self):
        so_list = self.env['sale.order'].search(
            [('date_order', '>=', self.start_date), ('date_order', '<=', self.end_date)]).ids
        so_tracking_list = self.env['sale.order'].search(
            [('date_order', '>=', self.start_date), ('date_order', '<=', self.end_date),('state', 'in', ['sale', 'done'])]).ids
        return {'domain': {'so_ids': [('id', 'in', so_list)],
                           'so_tracking_ids': [('id', 'in', so_tracking_list)]}}

    def view_sale_tracker_report(self):
        self.ensure_one()
        view = self.env.ref('panworld_sale.sale_tracker_view_tree')
        domain = []
        if self.start_date and self.end_date:
            domain = [('so_date', '<', self.end_date), ('so_date', '>', self.start_date)]
        if self.so_tracking_ids:
            domain += [('so_id', 'in', self.so_tracking_ids.ids)]
        view_id = view and view.id or False
        context = dict(self.env.context or {})
        return {
            'name': 'Sales tracker',
            'view_mode': 'list',
            'views': [(view_id, 'list')],
            'res_model': 'sales.tracker.report',
            'type': 'ir.actions.act_window',
            'domain': domain,
            'target': 'current',
            'context': context,
        }

    def create_attachment(self, file_name):
        """
        Delete file created in tmp dir, Delete old attachment and create attachment for download report
        :param file_name: file name string
        :return: attachment ir.attachment object
        """
        ir_attachment_obj = self.env['ir.attachment']
        # Read File data
        with open(f'/tmp/{file_name}', "rb+") as file:
            file_data = base64.encodebytes(file.read())
            file.close()

        # Remove tmp file
        os.remove(f'/tmp/{file_name}')

        # Delete Old Attachment
        attachments = ir_attachment_obj.search([('name', '=ilike', file_name),
                                                ('res_model', '=', 'sale.order')])
        attachments and attachments.unlink()

        return ir_attachment_obj.create({
            'name': file_name,
            'datas': file_data,
            'res_model': 'sale.order',
            'type': 'binary'
        })

    def export_so_data(self):
        """Method to export purchase order lines with difference for compare actions"""
        so_ids = self.so_ids
        if not so_ids:
            so_ids = self.env['sale.order'].search(
                [('company_id', '=', self.env.company.id), ('state', 'in', ['done', 'sale']),
                 ('date_order', '>=', self.start_date), ('date_order', '<=', self.end_date)])

        if so_ids:
            if self.partner_ids:
                so_ids = so_ids.filtered(lambda p: p.partner_id in self.partner_ids)

            if self.division_ids:
                so_ids = so_ids.filtered(lambda d: d.division_type_id in self.division_ids)

            if self.so_status:
                so_ids = so_ids.filtered(lambda s: s.so_status == self.so_status)

            report_file_name = self.with_context(so_ids=so_ids).prepare_so_lines_export_excel_data()
            # Create Attachment
            attachment = self.create_attachment(report_file_name)
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % attachment.id,
                'target': 'download',
            }

    def prepare_so_lines_export_excel_data(self):
        file_name = 'so_lines_data.xlsx'
        workbook = xlsxwriter.Workbook(f'/tmp/{file_name}')
        worksheet = workbook.add_worksheet("SOLinesData")
        # To protect some cells from being edited, like header field names title etc...
        # We can specify 'locked = False' in format to make cells editable
        # worksheet.protect()
        worksheet.set_landscape()
        worksheet.fit_to_pages(1, 0)
        worksheet.set_zoom(80)
        worksheet.set_column(0, 1, 20)
        worksheet.set_column(2, 2, 20)
        worksheet.set_column(3, 3, 15)
        worksheet.set_column(4, 4, 15)
        worksheet.set_column(5, 6, 20)
        worksheet.set_column(7, 7, 15)
        worksheet.set_column(8, 10, 22)
        worksheet.set_column(11, 19, 20)
        worksheet.set_column(20, 21, 30)
        worksheet.set_column(22, 28, 18)

        align_left = workbook.add_format({'align': 'left', 'valign': 'vcenter'})
        align_center = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
        align_center_date = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': True})
        cell_text_format = workbook.add_format(
            {'align': 'center', 'bold': True, 'size': 12, 'bg_color': '#BDD7EE',  'text_wrap': True})
        light_blue_body = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'bg_color': 'c6d9f1', 'border': 1})
        light_pink_body = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'bg_color': 'f2dcdb', 'border': 1})
        sky_blue_body = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'bg_color': 'dbeef4', 'border': 1})
        light_green_body = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'bg_color': 'd7e4bd', 'border': 1})
        pink_body = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'bg_color': 'e6b9b8', 'border': 1})
        blue_body = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'bg_color': 'b7dee8', 'border': 1})
        status_body = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bg_color': 'e6b9b8', 'border': 1})

        qty_data = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'locked': False})
        qty_data_lock = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        header_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': True, 'border': 1})

        row, col = 1, 1
        worksheet.write(1, 1, 'From Date', align_center_date)
        worksheet.write(1, 2, self.start_date.strftime('%d-%m-%Y'), align_center)
        worksheet.write(1, 4, 'To Date', align_center_date)
        worksheet.write(1, 5, self.end_date.strftime('%d-%m-%Y'), align_center)
        col += 1

        row, col = 3, 0
        worksheet.set_row(3, 30)
        header_lst = ['SO NO', 'SO Date', 'CSO Reference', 'CSO Date', 'Partner', 'Division', 'SO Currency',
                      'ISBN', 'Product Description', 'Quotation Quantity', 'Quote Cancel Qty', 'Order Quantity',
                      'Cancelled quantity', 'To Be Delivered Quantity', 'Backorder Quantity', 'Delivered Quantity', 'Invoiced Quantity',
                      'List Price', 'Discount', 'Unit Price', 'Quote Cancle Reason',
                      'Cancel Reason', 'Remarks', 'Pending Qty', 'Order Value', 'Delivered Value', 'Invoiced Value',
                      'Pending Inv Value', 'Status']
        for header in header_lst:
            # worksheet.set_column(row, col, len(header))
            worksheet.write(row, col, header, header_format)
            col += 1

        # Writing data
        col = 0
        row = 4
        so_ids = self.env.context and self.env.context.get('so_ids')
        for so_line in so_ids.mapped('order_line'):
            col = 0
            # New Adjustment date: 5 Jan 2024
            cancel_total = 0.0
            ######
            move = so_line.move_ids.filtered(lambda l: l.sale_line_id.id == so_line.id)
            cancel_move = so_ids.picking_ids.mapped('move_ids').filtered(lambda x: x.state == 'cancel')
            # New Adjustment date: 5 Jan 2024
            for rec in cancel_move:
                if rec.product_id.id == so_line.product_id.id and rec.picking_type_id.code == 'outgoing' and rec.location_id.usage == 'internal':
                    cancel_total += rec.product_uom_qty
            total_cancel_qty = cancel_total + so_line.cancelled_qty
            ###########
            #TODO : OLD Requirement change to change code.
            # if move.filtered(lambda l: l.state == 'cancel'):
            #     cancel_move = move.filtered(lambda l: l.state == 'cancel').mapped('product_uom_qty')
            # else:
            #     cancel_move = move.move_orig_ids.filtered(lambda l: l.state == 'cancel').mapped('product_uom_qty')
            done_qty = move.move_orig_ids.filtered(lambda l: l.state == 'done').mapped('product_uom_qty')
            picking_cancel_reason = move.move_orig_ids.filtered(lambda l: l.state == 'cancel')[
                        0].cancel_reason if move.move_orig_ids.filtered(lambda l: l.state == 'cancel') else ''
            so_cancel_reason = so_line.cancel_reason if so_line.cancel_reason else ""
            # cancel_reason = f"{picking_cancel_reason}, {so_cancel_reason}"
            cancel_reason = f"{picking_cancel_reason}{', ' if picking_cancel_reason else ''}{so_cancel_reason}"
            # Old backorder adj.
            # backorder_qty = so_line.product_uom_qty - sum(done_qty) if so_line.order_id.picking_ids.mapped(
            #     'backorder_id') and not so_line.move_ids.filtered(lambda l: l.state == 'cancel') else 0

            # New Backorder Adjustment date: 5 June 2024
            related_active_backorder = so_line.order_id.picking_ids.filtered(lambda x: x.backorder_id and x.state not in ['done', 'cancel'] and so_line.id in x.move_lines.sale_line_id.ids)
            backorder_demand_qty = 0
            if related_active_backorder:
                backorder_line = related_active_backorder.move_lines.filtered(lambda x: x.sale_line_id == so_line)
                if backorder_line:
                    backorder_demand_qty = sum(backorder_line.mapped('product_uom_qty'))
            # backorder_qty = so_line.product_uom_qty - sum(done_qty) if related_active_backorder and not so_line.move_ids.filtered(lambda l: l.state == 'cancel') else 0

            # pending_qty = round((so_line.so_quantity - so_line.cancelled_qty) - so_line.qty_delivered, 2)
            pending_qty = round((so_line.so_quantity - total_cancel_qty) - so_line.qty_delivered, 2)
            backorder_qty = min(pending_qty, backorder_demand_qty) if related_active_backorder and backorder_demand_qty > 0 and not so_line.move_ids.filtered(lambda l: l.state == 'cancel') else 0

            status = 'Closed' if pending_qty == 0 else 'Open'
            # order_value = round(so_line.quote_cancel_qty * so_line.discount, 2)
            # delivered_value = round(backorder_qty * so_line.discount, 2)
            # invoice_value = round(so_line.qty_delivered * so_line.discount, 2)
            # pending_inv_value = round((so_line.quote_cancel_qty - so_line.so_quantity) *
                                      # (so_line.discount - delivered_value))
            order_value = round(so_line.so_quantity * so_line.list_price, 2)
            delivered_value = round(so_line.qty_delivered * so_line.list_price, 2)
            invoice_value = round(so_line.qty_invoiced * so_line.list_price, 2)
            pending_inv_value = round(pending_qty * so_line.list_price, 2)

            worksheet.write(row, col, so_line.order_id.name or '', align_left)  # SO NO
            col += 1
            worksheet.write(row, col, so_line.order_id.date_order.strftime('%Y-%m-%d') if so_line.order_id.date_order else ' ', align_center)  # SO Date
            col += 1
            worksheet.write(row, col, so_line.order_id.customer_sales_order or '', align_left)  # CSO Reference
            col += 1
            worksheet.write(row, col, so_line.order_id.customer_so_date.strftime('%Y-%m-%d') if so_line.order_id.customer_so_date else ' ', align_center)  # CSO Date
            col += 1
            worksheet.write(row, col, so_line.order_id.partner_id.name if so_line.order_id.partner_id else ' ', align_left)  # Partner
            col += 1
            worksheet.write(row, col, so_line.order_id.division_type_id.name if so_line.order_id.division_type_id else ' ', align_left)  # Division
            col += 1
            worksheet.write(row, col, so_line.order_id.currency_id.name if so_line.order_id.currency_id else ' ', align_center)  # SO Currency
            col += 1
            worksheet.write(row, col, so_line.product_id.barcode, align_left)  # ISBN
            col += 1
            worksheet.write(row, col, so_line.product_id.name, align_left)  # Product Description
            col += 1
            worksheet.write(row, col, so_line.so_qty, light_blue_body)  # Quotation Quantity
            col += 1
            worksheet.write(row, col, so_line.quote_cancel_qty, light_blue_body)  # Quote Cancel Qty
            col += 1
            worksheet.write(row, col, so_line.so_quantity, light_blue_body)  # Order Quantity
            col += 1
            # worksheet.write(row, col, total_cancel_qty if cancel_move else so_line.cancelled_qty,
            worksheet.write(row, col, so_line.cancelled_qty,
                            light_blue_body)  # Cancelled quantity
            col += 1
            worksheet.write(row, col, so_line.product_uom_qty, light_blue_body)  # To Be Delivered Quantity
            col += 1
            worksheet.write(row, col, backorder_qty, light_pink_body)  # Backorder Quantity
            col += 1
            worksheet.write(row, col, so_line.qty_delivered, light_pink_body)  # Delivered Quantity
            col += 1
            worksheet.write(row, col, so_line.qty_invoiced, light_pink_body)  # Invoiced Quantity
            col += 1
            worksheet.write(row, col, so_line.price_unit, sky_blue_body)  # List Price
            col += 1
            worksheet.write(row, col, so_line.discount, sky_blue_body)  # Discount
            col += 1
            worksheet.write(row, col, so_line.list_price, sky_blue_body)  # Unit Price
            col += 1
            # worksheet.write(row, col, so_line.quote_cancel_reason if so_line.quote_cancel_reason else ' ', light_green_body)  # Quote Cancle Reason
            worksheet.write(row, col,
                            dict(so_line._fields['quote_cancel_reason'].selection).get(so_line.quote_cancel_reason, '')
                            if so_line.quote_cancel_reason else '', light_green_body)  # Quote Cancle Reason
            col += 1
            worksheet.write(row, col, cancel_reason if cancel_reason else '', light_green_body)   # Cancel Reason
            col += 1
            worksheet.write(row, col, ' ', light_green_body)  # Remarks
            col += 1
            # worksheet.write(row, col, so_line.order_id.pending_qty, pink_body)  # Pending Qty
            worksheet.write(row, col, pending_qty, pink_body)  # Pending Qty
            col += 1
            worksheet.write(row, col, order_value, blue_body)  # Order Value
            col += 1
            worksheet.write(row, col, delivered_value, blue_body)  # Delivered Value
            col += 1
            worksheet.write(row, col, invoice_value, blue_body)  # Invoiced Value
            col += 1
            worksheet.write(row, col, pending_inv_value, blue_body)  # Pending Inv Value
            col += 1
            worksheet.write(row, col, dict(so_line.order_id._fields['so_status'].selection).get(so_line.order_id.so_status, '')
                if so_line.order_id else '', status_body)  # Order Status
            # worksheet.write(row, col, status, status_body)  # Status
            row += 1

            # data = [so_line.order_id.name,  # SO NO
            #         so_line.order_id.date_order.strftime('%Y-%m-%d') if so_line.order_id.date_order else ' ',  # SO Date
            #         so_line.order_id.customer_sales_order,  # CSO Reference
            #         so_line.order_id.customer_so_date.strftime('%Y-%m-%d') if so_line.order_id.customer_so_date else ' ',  # CSO Date
            #         so_line.order_id.partner_id.name if so_line.order_id.partner_id else ' ',  # Partner
            #         so_line.order_id.division_type_id.name if so_line.order_id.division_type_id else ' ',  # Division
            #         so_line.order_id.currency_id.name if so_line.order_id.currency_id else ' ',  # SO Currency
            #         so_line.product_id.barcode,  # ISBN
            #         so_line.product_id.name,  # Product Description
            #         so_line.so_qty,  # Quotation Quantity
            #         so_line.quote_cancel_qty,  # Quote Cancel Qty
            #         so_line.so_quantity,  # Order Quantity
            #         so_line.product_uom_qty,  # To Be Delivered Quantity
            #         backorder_qty,  # Backorder Quantity
            #         so_line.qty_delivered,  # Delivered Quantity
            #         so_line.qty_invoiced,  # Invoiced Quantity
            #         so_line.price_unit,  # List Price
            #         so_line.discount,  # Discount
            #         so_line.list_price,  # Unit Price
            #         # sum(cancel_move) + so_line.cancelled_qty if cancel_move else so_line.cancelled_qty, #TODO : OLD Requirement change to change code.
            #         cancel_total + so_line.cancelled_qty if cancel_move else so_line.cancelled_qty,  # Cancelled quantity
            #         so_line.quote_cancel_reason if so_line.quote_cancel_reason else ' ',  # Quote Cancle Reason
            #         cancel_reason,  # Cancel Reason
            #         so_line.order_id.pending_qty,  # Pending Qty
            #         order_value,  # round(so_line.quote_cancel_qty * so_line.discount, 2),  # Order Value
            #         delivered_value,  # round('a' * so_line.discount, 2),  # Delivered Value
            #         invoice_value, #  round(so_line.qty_delivered * so_line.discount, 2),  # Invoiced Value
            #         pending_inv_value,  # Pending Inv Value
            #         dict(so_line.order_id._fields['so_status'].selection).get(so_line.order_id.so_status, '') if so_line.order_id else ''  # Order Status
            # ]
            # worksheet.write_row(row, col, data)
        worksheet.freeze_panes(4, 9)
        workbook.close()
        return file_name
