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
from datetime import datetime

import xlsxwriter

from odoo import _, exceptions, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

_logger = logging.getLogger(__name__)

try:
    import xlrd
except ImportError:
    _logger.debug("Cannot `import xlrd`.")
try:
    import base64
except ImportError:
    _logger.debug("Cannot `import base64`.")


class ImportSaleOrderWizard(models.TransientModel):
    _name = "import.sale.order.wizard"
    _description = "Import Sale Order Wizard"

    file = fields.Binary(string="Select File", help="Add excel file")
    sample_file = fields.Binary("Download File")
    file_name = fields.Char(string="File Name")

    def download_sample_file(self):
        # Method to download sample file for sale order import.
        name_of_file = "sample_sale_order_import.xls"
        fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xls")
        path_list = list(os.path.split(fp.name))
        path_list[len(path_list) - 1] = name_of_file
        file_path = os.path.join(*path_list)
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet()
        counter = 0
        field_list_to_import = [
            "Order Date",
            "Customer",
            "Analytical Account",
            "Product",
            "Quantity",
            "Unit Price",
            "Discount",
        ]
        for i in field_list_to_import:
            worksheet.write(0, counter, i)
            counter += 1
        workbook.close()
        export_id = base64.b64encode(open(file_path, "rb+").read())
        self.write({"sample_file": export_id, "file_name": name_of_file})
        return {
            "name": "Import Sale Order",
            "view_mode": "form",
            "res_id": self.id,
            "res_model": "import.sale.order.wizard",
            "view_type": "form",
            "type": "ir.actions.act_window",
            "target": "new",
        }

    def import_sale(self):
        # Import sale order from excel file
        if not self.file:
            raise UserError(_("Please upload file!."))
        sale_obj = self.env["sale.order"]
        partner_obj = self.env["res.partner"]
        product_obj = self.env["product.product"]
        analytic_account_obj = self.env["account.analytic.account"]
        try:
            fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
        except Exception:
            raise exceptions.UserError(_("Invalid file!"))
        so_dict_res = {}
        for rownum in range(sheet.nrows):
            if rownum >= 1:
                data = sheet.row_values(rownum)
                try:
                    create_date = data[0]
                    if create_date:
                        if type(create_date) is float:
                            create_date = datetime(
                                *xlrd.xldate_as_tuple(create_date, workbook.datemode)
                            )
                        else:
                            create_date_str = str(create_date)
                            create_date = datetime.strptime(
                                create_date_str, DATE_FORMAT
                            )
                    if not create_date:
                        raise UserError(
                            _("Please enter date in line number %s ", rownum + 1)
                        )
                    partner_name = str(int(data[1])) if isinstance(data[1], float) else str(data[1])
                    partner_rec = partner_obj.search(
                        [("name", "=", partner_name)], limit=1
                    )
                    if not partner_rec:
                        raise UserError(
                            _("Customer %s not found in system!", str(data[1]))
                        )
                    product_name = str(int(data[3])) if isinstance(data[3], float) else str(data[3])
                    product_rec = product_obj.search(
                        [("name", "=", product_name)], limit=1
                    )
                    if not product_rec:
                        raise UserError(
                            _("Product %s not found in system!", str(data[3]))
                        )
                    analytic_account_name = str(int(data[2])) if isinstance(data[2], float) else str(data[2])
                    analytic_account_rec = analytic_account_obj.search(
                        [("name", "=", analytic_account_name)], limit=1
                    )
                    if not analytic_account_rec:
                        raise UserError(
                            _("Analytic account %s not found in system!", str(data[2]))
                        )
                    product_uom_qty = data[4]
                    if product_uom_qty and type(product_uom_qty) is float:
                        product_uom_qty = product_uom_qty
                    else:
                        product_uom_qty = 0.0
                    price_unit = data[5]
                    if price_unit and type(price_unit) is float:
                        price_unit = price_unit
                    else:
                        price_unit = 0.0
                    discount = data[6]
                    if discount and type(discount) is float:
                        discount = discount
                    else:
                        discount = 0.0
                    if partner_rec.id not in so_dict_res:
                        so_dict_res[partner_rec.id] = {
                            "partner_id": partner_rec.id,
                            "date_order": create_date,
                            "analytic_account_id": analytic_account_rec.id,
                            "order_line": [
                                (
                                    0,
                                    0,
                                    {
                                        "product_id": product_rec.id,
                                        "product_uom_qty": product_uom_qty,
                                        "price_unit": price_unit,
                                        "discount": discount,
                                    },
                                )
                            ],
                        }
                    else:
                        so_dict_res[partner_rec.id]["order_line"] += [
                            (
                                0,
                                0,
                                {
                                    "product_id": product_rec.id,
                                    "product_uom_qty": product_uom_qty,
                                    "price_unit": price_unit,
                                    "discount": discount,
                                },
                            )
                        ]
                except Exception as e:
                    _logger.warning("Cannot import sale order.")
        so_list_res = list(so_dict_res.values())
        for rec in so_list_res:
            # Create SO base on excel file data.
            sale_obj.create(
                {
                    "partner_id": rec.get("partner_id"),
                    "date_order": rec.get("date_order"),
                    "is_imported": True,
                    "analytic_account_id": rec.get("analytic_account_id"),
                    "order_line": rec.get("order_line"),
                }
            )
