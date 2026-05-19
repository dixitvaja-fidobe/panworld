# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import models,_
import io
import base64
import xlsxwriter

class StockBackorderConfirmationInherit(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'
    _description = 'Backorder Confirmation'

    def process_cancel_backorder(self):
        pickings_to_validate = self.env.context.get('button_validate_picking_ids')
        if pickings_to_validate:
            pickings_to_validate = self.env['stock.picking'].browse(pickings_to_validate)
            self.action_generate_report(pickings_to_validate)
            return pickings_to_validate.with_context(skip_backorder=True, picking_ids_not_to_backorder=self.pick_ids.ids).button_validate()
        return True

    def action_generate_report(self, pickings_to_validate):
        for picking in pickings_to_validate:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet('Report')
            # bold = workbook.add_format({'bold': True})
            date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
            head = workbook.add_format(
                {'align': 'center', 'bold': True, 'font_size': '15px'})
            worksheet.merge_range('B2:I3', 'PENDING PRODUCTS  REPORT', head)
            worksheet.set_column('A:A', 25)
            worksheet.set_column('B:B', 40)
            worksheet.set_column('C:C', 15)
            worksheet.write('A5', 'Receive From')
            worksheet.write('B5', picking.partner_id.name)
            worksheet.write('A6', 'Received Date')
            worksheet.write('B6', picking.scheduled_date, date_format)
            worksheet.write('A7', 'PO')
            worksheet.write('B7', picking.origin)
            headers = {
                'isbn': 'ISBN',
                'product': 'Product Name',
                'demand': 'Demanded',
                'done': 'Done',
                'diff': 'Difference',
            }
            i = 8
            j = 0
            row = 9
            worksheet.write_row(row=i, col=j, data=headers.values())
            records = picking.move_ids.filtered(lambda line:line.quantity < line.product_uom_qty)
            for index, move in enumerate(records):
                worksheet.write(row + index, 0, move.product_id.barcode or '')
                worksheet.write(row + index, 1, move.product_id.name or '')
                worksheet.write_number(row + index, 2, move.product_uom_qty)
                worksheet.write_number(row + index, 3, move.quantity)
                worksheet.write_number(row + index, 4, move.product_uom_qty - move.quantity)
            workbook.close()
            xlsx_data = output.getvalue()
            output.close()
            # Optional: Save as attachment and download
            attachment = self.env['ir.attachment'].create({
                'name': 'No Backorder-Partial Delivery Report.xlsx',
                'type': 'binary',
                'datas': base64.b64encode(xlsx_data),
                'res_model': picking._name,
                'res_id': picking.id,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            })
            #Provide download URL
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'self',
            }

