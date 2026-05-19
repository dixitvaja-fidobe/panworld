import binascii
import logging
import os
import tempfile
import xlsxwriter
from odoo.exceptions import UserError
from odoo import _, fields, models
_logger = logging.getLogger(__name__)
try:
    import xlrd
except ImportError:
    _logger.debug("Cannot `import xlrd`.")
try:
    import base64
except ImportError:
    _logger.debug("Cannot `import base64`.")

class CheckPriceChange(models.TransientModel):
    _name = "check.price.change"
    _description = "Check Price Change"

    data_check_file = fields.Binary(string="Select File")

    def check_for_change(self):
        """ Function to check for the inconsistency in quantity, price and discount for the invoice from xlsx file """
        # Load the invoice and XLSX file
        try:
            file_stream = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
            file_stream.write(binascii.a2b_base64(self.data_check_file))
            file_stream.seek(0)
            workbook = xlrd.open_workbook(file_stream.name)
            sheet = workbook.sheet_by_index(0)
        except Exception:
            raise UserError(_("Please choose a valid XLSX file."))
        bill = self.env['account.move'].browse(int(self.env.context.get('active_id')))
        if not bill:
            raise UserError(_("No invoice found in the context."))
        # Extract expected barcodes from the file (column 0, skipping header)
        codes_in_file = [str(sheet.cell_value(i, 0)).split('.')[0] for i in range(1, sheet.nrows)]
        # Extract barcodes from the invoice lines
        invoice_lines = bill.invoice_line_ids
        invoice_barcodes = invoice_lines.mapped('product_id.barcode')
        # Check for mismatches
        extra_in_file = [code for code in codes_in_file if code not in invoice_barcodes]
        missing_in_file = [barcode for barcode in invoice_barcodes if barcode not in codes_in_file]
        if extra_in_file:
            raise UserError(_("No product(s) found in the invoice with ISBN:\n%s") % ', '.join(
                f"[{code}]" for code in extra_in_file))
        if missing_in_file:
            raise UserError(_("The product(s) below are missing in the file with ISBN:\n%s") % ', '.join(
                f"[{barcode}]" for barcode in missing_in_file))
        # Check for changes in quantity, price, and discount
        diffs = []
        for i in range(1, sheet.nrows):
            row = sheet.row_values(i)
            barcode = str(int(row[0]))
            quantity, price, discount = row[1], row[2], row[3]
            matching_line = invoice_lines.filtered(lambda l: l.product_id.barcode == barcode)
            if not matching_line:
                continue  # Should not happen if prior check passed
            line = matching_line[0]  # One product line per barcode
            if line.quantity != quantity or line.price_unit != price or line.discount != discount:
                diffs.append(f"\n\t[{barcode}] at line {i + 1}")
        if diffs:
            raise UserError(_("Changes found in the Excel file for the ISBN(s):\n%s") % ''.join(diffs))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'SUCCESS',
                'message': 'File is matching with the in the Prices and Discounts in the draft invoice',
                'type': 'success',
                'sticky': False,
            }
        }
    def export_data(self):
        """Method to download a file with only titles for compare action"""
        report_file_name = self.prepare_account_move_export_excel_data()
        # Create Attachment
        attachment = self.create_attachment(report_file_name)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'download',
        }

    def prepare_account_move_export_excel_data(self):
        """Prepare the excel sheet"""
        file_name = 'Bill Lines.xlsx'
        workbook = xlsxwriter.Workbook(f'/tmp/{file_name}')
        worksheet = workbook.add_worksheet("BillLinesData")
        worksheet.set_landscape()
        worksheet.protect()
        worksheet.fit_to_pages(1, 0)
        worksheet.set_zoom(80)
        worksheet.set_column(1, 1, 20)
        worksheet.set_column(2, 2, 20)
        worksheet.set_column(3, 3, 15)
        worksheet.set_column(4, 4, 15)
        worksheet.set_column(6, 6, 20)

        qty_data = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'locked': False})
        qty_data_lock = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        header_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'bold': True, 'border': 1})

        row, col = 0, 0
        worksheet.set_row(1, 30)
        worksheet.write(row, col, 'ISBN', header_format)
        col += 1
        worksheet.write(row, col, 'QTY', header_format)
        col += 1
        worksheet.write(row, col, 'LIST PRICE', header_format)
        col += 1
        worksheet.set_column(col, col, 40)
        worksheet.write(row, col, 'DISCOUNT', header_format)
        col += 1
        workbook.close()
        return file_name

    def create_attachment(self, file_name):
        """
         Return: attachment ir.attachment object
        """
        ir_attachment_obj = self.env['ir.attachment']
        # Read File data
        with open(f'/tmp/{file_name}', "rb+") as file:
            file_data = base64.encodebytes(file.read())
            file.close()
        os.remove(f'/tmp/{file_name}')
        return ir_attachment_obj.create({
            'name': file_name,
            'datas': file_data,
            'type': 'binary'
        })