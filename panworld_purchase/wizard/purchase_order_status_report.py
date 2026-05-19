import xlsxwriter
from odoo.exceptions import UserError
from odoo import models, fields, api, exceptions, _
import base64
import binascii
import logging
import os
import tempfile

class PurchaseOrderStatusReport(models.TransientModel):
    _name = 'purchase.order.status.report'
    _description = 'Purchase Order status report'

    start_date = fields.Date(string='Start Date', default=fields.Date.today(), required=True)
    end_date = fields.Date(string='End Date', default=fields.Date.today(), required=True)
    po_ids = fields.Many2many('purchase.order', string="Purchase Order")
    partner_ids = fields.Many2many('res.partner', string="Customer")

    @api.onchange('start_date', 'end_date')
    def onchange_start_end_date(self):
        po_list = self.env['purchase.order'].search(
            [('date_approve', '>=', self.start_date), ('date_approve', '<=', self.end_date)])
        partner_po_list = self.env['res.partner'].search([('id', 'in', po_list.mapped('partner_id').ids)])
        return {'domain': {'po_ids': [('id', 'in', po_list.ids)], 'partner_ids': [('id', 'in', partner_po_list.ids)]}}


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
                                                ('res_model', '=', 'purchase.order')])
        attachments and attachments.unlink()

        return ir_attachment_obj.create({
            'name': file_name,
            'datas': file_data,
            'res_model': 'purchase.order',
            'type': 'binary'
        })

    def export_po__data(self):
        """Method to export purchase order lines with difference for compare actions"""
        po_ids = self.po_ids
        if not po_ids:
            po_ids = self.env['purchase.order'].search(
                [('date_approve', '>=', self.start_date), ('date_approve', '<=', self.end_date),
                 ('company_id', '=', self.env.company.id), ('state', 'in', ['done', 'purchase'])])
        if po_ids:
            if self.partner_ids:
                po_ids = po_ids.filtered(lambda p: p.partner_id in self.partner_ids)

            report_file_name = self.with_context(po_ids=po_ids).prepare_po_lines_export_excel_data()
            # Create Attachment
            attachment = self.create_attachment(report_file_name)
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % attachment.id,
                'target': 'download',
            }

    def prepare_po_lines_export_excel_data(self):
        file_name = 'po_lines_data.xlsx'
        workbook = xlsxwriter.Workbook(f'/tmp/{file_name}')
        worksheet = workbook.add_worksheet("POLinesData")
        # To protect some cells from being edited, like header field names title etc...
        # We can specify 'locked = False' in format to make cells editable
        # worksheet.protect()
        worksheet.set_landscape()
        worksheet.fit_to_pages(1, 0)
        worksheet.set_zoom(80)
        worksheet.set_column(0, 1, 17)
        worksheet.set_column(2, 2, 24)
        worksheet.set_column(3, 3, 15)
        worksheet.set_column(4, 4, 15)
        worksheet.set_column(5, 6, 20)
        worksheet.set_column(7, 7, 15)
        worksheet.set_column(8, 10, 22)
        worksheet.set_column(11, 17, 20)
        worksheet.set_column(18, 19, 23)
        worksheet.set_column(20, 21, 30)
        worksheet.set_column(22, 23, 18)
        worksheet.set_column(24, 25, 25)

        align_left = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'text_wrap': True})
        align_right = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'text_wrap': True})
        align_center = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        align_center_date = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': True})
        qty_data = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'locked': False})
        qty_data_lock = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        header_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': True, 'border': 1})

        light_blue_body = workbook.add_format(
            {'align': 'right', 'valign': 'vcenter', 'bg_color': 'c6d9f1', 'border': 1})
        light_pink_body = workbook.add_format(
            {'align': 'right', 'valign': 'vcenter', 'bg_color': 'f2dcdb', 'border': 1})
        sky_blue_body = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'bg_color': 'dbeef4', 'border': 1})
        light_green_body = workbook.add_format(
            {'align': 'right', 'valign': 'vcenter', 'bg_color': 'd7e4bd', 'border': 1})
        pink_body = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'bg_color': 'e6b9b8', 'border': 1})
        blue_body = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'bg_color': 'b7dee8', 'border': 1})
        status_body = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bg_color': 'e6b9b8', 'border': 1})

        row, col = 1, 1
        worksheet.write(1, 1, 'From Date', align_center_date)
        worksheet.write(1, 2, self.start_date.strftime('%d-%m-%Y'), align_center)
        worksheet.write(1, 4, 'To Date', align_center_date)
        worksheet.write(1, 5, self.end_date.strftime('%d-%m-%Y'), align_center)
        col += 1

        row, col = 3, 0
        worksheet.set_row(3, 30)
        header_lst = ['PO NO', 'PO Date', 'Partner', 'PO Currency', 'ISBN', 'Product Description', 'RFQ Quantity',
                      'Order Quantity', 'Cancelled quantity', 'Received Quantity', 'Billed Quantity',
                      'Back order Quantity', 'PO List Price', 'PO Discount', 'PO Unit Price', 'Bill List Price',
                      'Bill Discount', 'Bill Unit Price', 'Customer Sales Order', 'Customer Name', 'Related SO',
                      'Cancel Reason', 'Pending Qty', 'PO Status', 'Po & Bill Price Diff/ Unit',
                      'Total Price Var PO Vs Bill']
        for header in header_lst:
            worksheet.write(row, col, header, header_format)
            col += 1
        # Writing data
        col = 0
        row = 4
        po_ids = self.env.context and self.env.context.get('po_ids')
        for po_line in po_ids.mapped('order_line'):
            col = 0
            move = po_line.move_ids.filtered(lambda l: l.purchase_line_id.id == po_line.id)
            if move.filtered(lambda l: l.state == 'cancel'):
                cancel_move = move.filtered(lambda l: l.state == 'cancel').mapped('product_uom_qty')
                picking_cancel_reason = move.filtered(lambda l: l.state == 'cancel')[
                            0].cancel_reason if move.filtered(lambda l: l.state == 'cancel') else ''
            else:
                cancel_move = move.move_orig_ids.filtered(lambda l: l.state == 'cancel').mapped('product_uom_qty')
                picking_cancel_reason = move.move_orig_ids.filtered(lambda l: l.state == 'cancel')[
                            0].cancel_reason if move.move_orig_ids.filtered(lambda l: l.state == 'cancel') else ''
            po_cancel_reason = po_line.cancel_reason if po_line.cancel_reason else ""
            # cancel_reason = f"{picking_cancel_reason}, {po_cancel_reason}"
            cancel_reason = f"{picking_cancel_reason}{', ' if picking_cancel_reason else ''}{po_cancel_reason}"

            # Task - 02907
            # po_qty = po_line.move_ids.filtered(lambda l: l.state == 'done')
            # qty = sum(po_qty.product_uom_qty for po_qty in po_qty)
            #T04425 backorder qty
            backorder_picking = po_line.order_id.picking_ids.filtered(lambda l: l.state in ['waiting', 'confirmed', 'assigned'] and l.backorder_id)
            # backorder_qty = backorder_picking.move_ids.filtered(
            #     lambda m: m.product_id == po_line.product_id).product_uom_qty
            move_qty_records = backorder_picking.move_ids.filtered(
                lambda m: m.product_id == po_line.product_id)
            move_qty_values = move_qty_records.mapped('product_uom_qty')
            if move_qty_values:
                backorder_qty = sum(move_qty_values)
            else:
                backorder_qty = 0
            po_and_bill_price_diff = round(po_line.po_price - po_line.price_unit, 2)
            # price_var_po_vs_bill = (po_line.po_price - po_line.price_unit) * po_line.qty_received
            price_var_po_vs_bill = round(po_and_bill_price_diff * po_line.qty_invoiced, 2)

            worksheet.write(row, col, po_line.order_id.name, align_left)  # PO NO
            col += 1
            worksheet.write(row, col,
                            po_line.order_id.date_order.strftime('%Y-%m-%d') if po_line.order_id.date_order else ' ',
                            align_center)  # PO Date
            col += 1
            worksheet.write(row, col, po_line.order_id.partner_id.name if po_line.order_id.partner_id else '',
                            align_left)  # Partner
            col += 1
            worksheet.write(row, col, po_line.currency_id.name if po_line.currency_id else '',
                            align_center)  # PO Currency
            col += 1
            worksheet.write(row, col, po_line.product_id.barcode, align_left)  # ISBN
            col += 1
            worksheet.write(row, col, po_line.product_id.name, align_left)  # Product Description
            col += 1
            worksheet.write(row, col, po_line.rfq_qty, light_blue_body)  # RFQ Quantity
            col += 1
            worksheet.write(row, col, po_line.po_qty, light_blue_body)  # Order Quantity
            col += 1
            worksheet.write(row, col, sum(cancel_move) + po_line.cancel_qty if cancel_move else po_line.cancel_qty,
                            light_blue_body)  # Cancelled quantity
            col += 1
            worksheet.write(row, col, po_line.qty_received, light_pink_body)  # Received Quantity
            col += 1
            worksheet.write(row, col, po_line.qty_invoiced, light_pink_body)  # Billed Quantity
            col += 1
            worksheet.write(row, col, backorder_qty if backorder_picking else 0, light_pink_body)  # Back order Quantity
            col += 1
            worksheet.write(row, col, po_line.po_list_price, sky_blue_body)  # PO List Price
            col += 1
            worksheet.write(row, col, po_line.po_discount, sky_blue_body)  # PO Discount
            col += 1
            worksheet.write(row, col, po_line.po_price, sky_blue_body)  # PO Unit Price
            col += 1
            worksheet.write(row, col, po_line.list_price, light_green_body)  # Bill List Price
            col += 1
            worksheet.write(row, col, po_line.discount, light_green_body)  # Bill Discount
            col += 1
            worksheet.write(row, col, po_line.price_unit, light_green_body)  # Bill Unit Price
            col += 1
            worksheet.write(row, col, po_line.customer_sales_order if po_line.customer_sales_order else ' ',
                            blue_body)  # Customer Sales Order
            col += 1
            worksheet.write(row, col, po_line.customer_name if po_line.customer_name else ' ',
                            blue_body)  # Customer Name
            col += 1
            worksheet.write(row, col, po_line.related_so.name if po_line.related_so else '', blue_body)  # Related SO
            col += 1
            worksheet.write(row, col, cancel_reason if cancel_reason else ' ', blue_body)  # Cancel Reason
            col += 1
            worksheet.write(row, col, po_line.order_id.po_pending_qty, align_right)  # Pending Qty
            col += 1
            worksheet.write(row, col,
                            dict(po_line.order_id._fields['po_status'].selection).get(po_line.order_id.po_status, '')
                            if po_line.order_id else '', align_center)  # PO Status
            col += 1
            worksheet.write(row, col, po_and_bill_price_diff, light_green_body)  # 'Po & Bill Price Diff/ Unit',
            col += 1
            worksheet.write(row, col, price_var_po_vs_bill, pink_body)  # Total Price Var PO Vs Bill
            col += 1
            # data = [po_line.order_id.name,
            #         '',
            #         '',
            #         '',
            #         po_line.product_id.barcode,
            #         po_line.product_id.name,
            #         po_line.rfq_qty,
            #         po_line.po_qty,
            #         po_line.qty_received,
            #         po_line.qty_invoiced,
            #         sum(cancel_move) + po_line.cancel_qty if cancel_move else po_line.cancel_qty,
            #         # po_line.product_qty - po_line.qty_received + po_line.cancel_qty if po_line.move_ids.filtered(lambda l: l.state == 'cancel') and po_line.move_ids.filtered(lambda l: l.state == 'cancel')[0].cancel_reason else po_line.cancel_qty,
            #         # po_line.product_qty - po_line.qty_received if po_line.action == 'backorder' else 0,
            #         backorder_qty if backorder_picking else 0,
            #         po_line.po_list_price,
            #         po_line.po_discount,
            #         po_line.po_price,
            #         po_line.list_price,
            #         po_line.discount,
            #         po_line.price_unit,
            #         po_line.po_price - po_line.price_unit,
            #         po_line.customer_sales_order or '',
            #         po_line.customer_name or '',
            #         # po_line.sale_reference or '',
            #         '',
            #         cancel_reason,
            #         '',
            #         '',
            #         '',
            #         # po_line.move_ids.filtered(lambda l: l.state == 'cancel')[0].cancel_reason if po_line.move_ids.filtered(lambda l: l.state == 'cancel') else '',
            #         ]
            # worksheet.write_row(row, col, data)
            row += 1
        worksheet.freeze_panes(4, 6)
        workbook.close()
        return file_name
