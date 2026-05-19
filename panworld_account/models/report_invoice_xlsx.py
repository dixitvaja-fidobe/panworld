# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################
from odoo import models


class ReportInvoiceXlsx(models.AbstractModel):
    _name = 'report.panworld_account.report_invoice_panworld_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, invoices):
        for invoice in invoices:
            sheet = workbook.add_worksheet(invoice.name or 'Invoice')
            bold = workbook.add_format({'bold': True})
            # Header Info
            sheet.write(0, 0, 'Customer', bold)
            sheet.write(0, 1, invoice.partner_id.name)
            sheet.write(1, 0, 'Invoice Number', bold)
            sheet.write(1, 1, invoice.name)
            sheet.write(2, 0, 'Invoice Date', bold)
            sheet.write(2, 1, str(invoice.invoice_date))
            sheet.write(3, 0, 'Total Amount', bold)
            sheet.write(3, 1, invoice.amount_total)
            sheet.write(4, 0, 'CSO Reference', bold)
            sheet.write(4, 1, invoice.tracking_ref)
            sheet.set_column('A:I', 20)
            headers = [
                'ISBN', 'Product Name', 'Quantity', 'List Price',
                'Discount', 'Unit Price', 'Taxes', 'VAT Amt', 'Subtotal'
            ]
            sheet.write_row(6, 0, headers, bold)
            for idx, line in enumerate(invoice.invoice_line_ids, start=7):
                isbn = line.product_id.barcode or ''
                product_name = line.product_id.name or ''
                qty = line.quantity
                list_price = line.price_unit
                discount = line.discount
                unit_price = list_price * (1 - discount / 100.0)
                tax_names = ', '.join(t.name for t in line.tax_ids)
                taxes = line.tax_ids.compute_all(
                    line.price_unit, invoice.currency_id, line.quantity,
                    product=line.product_id, partner=invoice.partner_id
                )['taxes']
                vat_amt = sum(t['amount'] for t in taxes)
                subtotal = line.price_subtotal
                sheet.write(idx, 0, isbn)
                sheet.write(idx, 1, product_name)
                sheet.write_number(idx, 2, qty)
                sheet.write_number(idx, 3, list_price)
                sheet.write_number(idx, 4, discount)
                sheet.write_number(idx, 5, unit_price)
                sheet.write(idx, 6, tax_names)
                sheet.write_number(idx, 7, vat_amt)
                sheet.write_number(idx, 8, subtotal)
