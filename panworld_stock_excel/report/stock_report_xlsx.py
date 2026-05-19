# -*- coding: utf-8 -*-
from odoo import models

class StockReportXlsx(models.AbstractModel):
    _name = 'report.panworld_stock_excel.report_stock_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Stock Excel Report'

    def generate_xlsx_report(self, workbook, data, wizard):
        sheet = workbook.add_worksheet('Stock Report')
        
        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#D3D3D3',
            'border': 1
        })
        data_format = workbook.add_format({
            'border': 1,
            'align': 'left'
        })
        number_format = workbook.add_format({
            'border': 1,
            'align': 'right',
            'num_format': '#,##0.00'
        })

        # Headers
        headers = [
            'Warehouse', 'Location', 'Internal Reference', 'Product', 
            'On Hand Quantity', 'Reserved Quantity', 'Available Quantity', 'UoM'
        ]
        for col_num, header in enumerate(headers):
            sheet.write(0, col_num, header, header_format)
            sheet.set_column(col_num, col_num, 20)

        # Get stock quants for all internal locations
        domain = [
            ('location_id.usage', '=', 'internal'),
        ]
        if wizard.product_id:
            domain.append(('product_id', '=', wizard.product_id.id))
        
        quants = self.env['stock.quant'].search(domain)

        row = 1
        for quant in quants:
            warehouse = quant.location_id.warehouse_id.name or 'N/A'
            location = quant.location_id.complete_name
            product_ref = quant.product_id.default_code or ''
            product_name = quant.product_id.display_name
            on_hand = quant.quantity
            reserved = quant.reserved_quantity
            available = quant.available_quantity
            uom = quant.product_uom_id.name

            sheet.write(row, 0, warehouse, data_format)
            sheet.write(row, 1, location, data_format)
            sheet.write(row, 2, product_ref, data_format)
            sheet.write(row, 3, product_name, data_format)
            sheet.write(row, 4, on_hand, number_format)
            sheet.write(row, 5, reserved, number_format)
            sheet.write(row, 6, available, number_format)
            sheet.write(row, 7, uom, data_format)
            row += 1
