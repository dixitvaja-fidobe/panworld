# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockExcelReportWizard(models.TransientModel):
    _name = 'stock.excel.report.wizard'
    _description = 'Stock Excel Report Wizard'

    product_id = fields.Many2one('product.product', string='Product', help="Select a product to filter the report. Leave empty for all products.")

    def action_download_xlsx(self):
        return self.env.ref('panworld_stock_excel.action_report_stock_xlsx').report_action(self)
