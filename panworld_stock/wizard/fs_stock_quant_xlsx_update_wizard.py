# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import io
import logging

try:
    import openpyxl
except ImportError:
    openpyxl = None

_logger = logging.getLogger(__name__)

class StockQuantXlsxUpdateWizard(models.TransientModel):
    _name = 'fs.stock.quant.xlsx.update.wizard'
    _description = 'Update Stock Quants via XLSX'

    excel_file = fields.Binary(string='XLSX File', required=True)
    file_name = fields.Char(string='File Name')

    def action_apply(self):
        self.ensure_one()
        if not openpyxl:
            raise UserError(_("The 'openpyxl' library is not installed. Please contact your administrator."))

        if not self.excel_file:
            raise UserError(_("Please upload an XLSX file."))

        try:
            file_content = base64.b64decode(self.excel_file)
            workbook = openpyxl.load_workbook(io.BytesIO(file_content), data_only=True)
            sheet = workbook.active
        except Exception as e:
            raise UserError(_("Error reading the XLSX file: %s") % str(e))

        # Expected columns: Product Code, Location, Stock
        # We skip the header row
        rows = list(sheet.rows)
        if len(rows) <= 1:
            raise UserError(_("The file is empty or only contains a header."))

        header = [str(cell.value).strip().lower() if cell.value else "" for cell in rows[0]]
        _logger.info("XLSX Header: %s", header)

        try:
            # Find column indices based on headers
            prod_idx = header.index('product')
            loc_idx = header.index('location')
            qty_idx = header.index('qty')
        except ValueError:
            raise UserError(_("The XLSX file must contain headers: 'Product', 'Location', and 'Qty'."))

        updates_count = 0
        for row_idx, row in enumerate(rows[1:], start=2):
            product_code = str(row[prod_idx].value).strip() if row[prod_idx].value else None
            location_name = str(row[loc_idx].value).strip() if row[loc_idx].value else None
            stock_qty = row[qty_idx].value

            if not product_code:
                raise UserError(_("Row %s: Missing product code.") % row_idx)
            if not location_name:
                raise UserError(_("Row %s: Missing location name.") % row_idx)

            # 1. Find Product
            product = self.env['product.product'].sudo().search([('default_code', '=', product_code)], limit=1)
            if not product:
                raise UserError(_("Row %s: Product with code '%s' not found.") % (row_idx, product_code))

            # 2. Find Location
            location = self.env['stock.location'].sudo().search([('complete_name', '=', location_name)], limit=1)
            if not location:
                raise UserError(_("Row %s: Location '%s' not found.") % (row_idx, location_name))

            try:
                qty = float(stock_qty) if stock_qty is not None else 0.0
            except (ValueError, TypeError):
                raise UserError(_("Row %s: Invalid stock quantity '%s'.") % (row_idx, stock_qty))

            # 3. Update or Create Quant via SQL (Direct update to bypass inventory adjustments)
            quants = self.env['stock.quant'].sudo().search([
                ('product_id', '=', product.id),
                ('location_id', '=', location.id)
            ])

            if quants:
                # Update first quant, zero others
                target_quant = quants[0]
                self.env.cr.execute(
                    "UPDATE stock_quant SET quantity = %s WHERE id = %s",
                    (qty, target_quant.id)
                )
                if len(quants) > 1:
                    other_ids = tuple(quants[1:].ids)
                    self.env.cr.execute(
                        "UPDATE stock_quant SET quantity = 0 WHERE id IN %s",
                        (other_ids,)
                    )
            else:
                # Create new quant
                company_id = location.company_id.id or self.env.company.id
                self.env.cr.execute(
                    """INSERT INTO stock_quant (product_id, location_id, quantity, reserved_quantity, company_id, in_date) 
                       VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)""",
                    (product.id, location.id, qty, 0.0, company_id)
                )
            
            updates_count += 1

        # Invalidate cache
        self.env['stock.quant'].invalidate_model(['quantity'])

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Successfully updated %s stock records.') % updates_count,
                'type': 'success',
                'sticky': False,
            }
        }
