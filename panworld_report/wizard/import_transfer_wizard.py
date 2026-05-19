# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
import binascii
import logging
import os
import tempfile

import xlsxwriter

from odoo import _, exceptions, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

try:
    import xlrd
except ImportError:
    _logger.debug("Cannot `import xlrd`.")
try:
    import base64
except ImportError:
    _logger.debug("Cannot `import base64`.")


class ImportTransfers(models.TransientModel):
    _name = "import.transfers.wizard"
    _description = "Internal Transfer-Bulk"

    file = fields.Binary(string="Select File", help="Add excel file")
    sample_file = fields.Binary("Download File")
    file_name = fields.Char(string="File Name")

    def download_sample_file(self):
        # Method to download sample file for transfers import.
        name_of_file = "sample_transfers_import.xls"
        fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xls")
        path_list = list(os.path.split(fp.name))
        path_list[len(path_list) - 1] = name_of_file
        file_path = os.path.join(*path_list)
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet()
        counter = 0
        field_list_to_import = [
            "Operation type",
            "Source Location",
            "Destination Location",
            "ISBN",
            "QTY",
            "Company",
        ]
        for i in field_list_to_import:
            worksheet.write(0, counter, i)
            counter += 1
        workbook.close()
        export_id = base64.b64encode(open(file_path, "rb+").read())
        self.write({"sample_file": export_id, "file_name": name_of_file})
        return {
            "name": "Internal Transfer-Bulk",
            "view_mode": "form",
            "res_id": self.id,
            "res_model": "import.transfers.wizard",
            "view_type": "form",
            "type": "ir.actions.act_window",
            "target": "new",
        }

    def is_number(self, data):
        try:
            data = float(data)
            if isinstance(data, float):
                return True
        except ValueError:
            return False

    def validate_and_get_item_code(self, isbn):
        """Method to get isbn(barcode) code of product"""
        if not isbn:
            raise UserError(_("Isbn is required."))
        # Ensure it's a string and strip .0 if it came from a float
        if isinstance(isbn, float):
            isbn = str(int(isbn))
        else:
            isbn = str(isbn).strip()
        if len(isbn) <= 0:
            raise UserError(_("Isbn is required."))
        return isbn


    def import_transfers(self):
        # Import transfers from excel file
        if not self.file:
            raise UserError(_("Please upload file!."))
        
        picking_obj = self.env["stock.picking"]
        product_obj = self.env["product.product"]
        company_obj = self.env["res.company"]
        picking_type_obj = self.env["stock.picking.type"]
        location_obj = self.env["stock.location"]

        try:
            file_data = base64.b64decode(self.file)
            workbook = xlrd.open_workbook(file_contents=file_data)
            sheet = workbook.sheet_by_index(0)
        except Exception as e:
            _logger.error("Import Transfer Error: %s", e)
            if "xlsx file; not supported" in str(e):
                raise exceptions.UserError(_("The uploaded file is in XLSX format, which is not supported by the 'xlrd' library version on this server. Please save the file as 'Excel 97-2003 Workbook (.xls)' and try again."))
            raise exceptions.UserError(_("Invalid file! Detail: %s") % str(e))

        # --- PHASE 1: Pre-fetch all data from Excel ---
        all_rows_data = []
        company_names = set()
        op_type_names = set()
        location_names = set()
        isbns = set()

        for rownum in range(1, sheet.nrows):
            data = sheet.row_values(rownum)
            if not any(data): continue # Skip empty rows
            
            c_name = str(int(data[5])) if isinstance(data[5], float) else str(data[5]).strip()
            op_name = str(int(data[0])) if isinstance(data[0], float) else str(data[0]).strip()
            src_name = str(int(data[1])) if isinstance(data[1], float) else str(data[1]).strip()
            dest_name = str(int(data[2])) if isinstance(data[2], float) else str(data[2]).strip()
            isbn = self.validate_and_get_item_code(isbn=data[3])
            qty = data[4] if isinstance(data[4], (int, float)) else 0.0

            all_rows_data.append({
                'c_name': c_name, 'op_name': op_name, 'src_name': src_name,
                'dest_name': dest_name, 'isbn': isbn, 'qty': qty, 'rownum': rownum + 1
            })
            company_names.add(c_name)
            op_type_names.add(op_name)
            location_names.add(src_name)
            location_names.add(dest_name)
            isbns.add(isbn)

        # --- PHASE 2: Bulk Database Lookups ---
        companies = {c.name: c for c in company_obj.search([('name', 'in', list(company_names))])}
        
        # Prefetch picking types and locations using company filters if possible
        all_companies_ids = [c.id for c in companies.values()]
        picking_types = {(pt.name, pt.company_id.id): pt for pt in picking_type_obj.search([
            ('name', 'in', list(op_type_names)), ('company_id', 'in', all_companies_ids)])}
        
        locations = {(loc.name, loc.company_id.id): loc for loc in location_obj.search([
            ('name', 'in', list(location_names)), ('company_id', 'in', all_companies_ids)])}

        # Products search (Barcode, Internal Ref, or Name)
        product_list = product_obj.search(['|', '|', ('barcode', 'in', list(isbns)), ('default_code', 'in', list(isbns)), ('name', 'in', list(isbns))])
        products = {}
        for p in product_list:
            if p.barcode: products[p.barcode] = p
            if p.default_code: products[p.default_code] = p
            if p.name: products[p.name] = p

        # --- PHASE 3: Process data and Group by Transfer ---
        transfer_dict = {}
        for row in all_rows_data:
            company = companies.get(row['c_name'])
            if not company:
                raise UserError(_("Company %s not found (Line %s)") % (row['c_name'], row['rownum']))
            
            pt = picking_types.get((row['op_name'], company.id))
            if not pt:
                raise UserError(_("Operation Type %s not found for %s (Line %s)") % (row['op_name'], company.name, row['rownum']))
            
            src_loc = locations.get((row['src_name'], company.id))
            dest_loc = locations.get((row['dest_name'], company.id))
            if not src_loc or not dest_loc:
                missing = row['src_name'] if not src_loc else row['dest_name']
                raise UserError(_("Location %s not found (Line %s)") % (missing, row['rownum']))
            
            product = products.get(row['isbn'])
            if not product:
                raise UserError(_("Product ISBN %s not found (Line %s)") % (row['isbn'], row['rownum']))

            # Grouping Key: Picking Type + Source + Dest
            group_key = (pt.id, src_loc.id, dest_loc.id)
            if group_key not in transfer_dict:
                transfer_dict[group_key] = {
                    'picking_type_id': pt.id,
                    'location_id': src_loc.id,
                    'location_dest_id': dest_loc.id,
                    'company_id': company.id,
                    'is_imported': True,
                    'move_ids': []
                }
            
            transfer_dict[group_key]['move_ids'].append((0, 0, {
                'product_id': product.id,
                'product_uom': product.uom_id.id,
                'product_uom_qty': row['qty'],
                'location_id': src_loc.id,
                'location_dest_id': dest_loc.id,
            }))

        # --- PHASE 4: Batch Create ---
        if transfer_dict:
            picking_obj.create(list(transfer_dict.values()))
        
        return True
