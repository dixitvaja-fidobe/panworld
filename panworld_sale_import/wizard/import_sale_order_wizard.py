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
    _inherit = "import.sale.order.wizard"

    is_use_marketplace_values = fields.Boolean(
        string="Use Marketplace Values",
        help="Use mco and oco cost configured in marketplace",
    )

    def download_sample_file(self):
        """
            Override method to pass panworld custom fields values (
            Customer Sales Order, MCO, SCO and OCO).
        """
        name_of_file = "sample_sale_order_import.xls"
        fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xls")
        path_list = list(os.path.split(fp.name))
        path_list[len(path_list) - 1] = name_of_file
        file_path = os.path.join(*path_list)
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet()
        counter = 0
        field_list_to_import = [
            "ID", # Add as per new requirement : 23/01/2024
            "Sales Order Date",
            "Delivery Date",
            "Customer Sales Order",
            "Customer",
            "Analytical Account",
            "MCO",
            "SCO",
            "OCO",
            "Quotation qty", # Add as per new requirement : 23/01/2024
            "SO quantity", # Add as per new requirement : 23/01/2024
            "Product(isbn)",
            "Quantity",
            "List Price",
            "Discount",
            "Analytic Tags",
            "Course ID",
            "CRN",
            "C.S.N",
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
        """
            Override method to pass panworld custom fields values (
            Customer Sales Order, MCO, SCO and OCO).
        """
        if not self.file:
            raise UserError(_("Please upload file!."))
        sale_obj = self.env["sale.order"]
        partner_obj = self.env["res.partner"]
        product_obj = self.env["product.product"]
        analytic_account_obj = self.env["account.analytic.account"]
        analytic_tag_obj = self.env["account.analytic.tag"]
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
                    create_date = data[1]
                    if create_date:
                        if type(create_date) is float:
                            create_date = datetime(
                                *xlrd.xldate_as_tuple(create_date, workbook.datemode)
                            )
                        else:
                            create_date_str = str(create_date)
                            try:
                                create_date = datetime.strptime(
                                    create_date_str, DATE_FORMAT
                                )
                            except Exception:
                                raise exceptions.UserError(_(
                                    "Sale order date should be in 'yy-mm-dd' format in line number %s!", rownum + 1))
                    if not create_date:
                        raise UserError(
                            _("Please add date in line number %s ", rownum + 1)
                        )
                    delivery_date = data[2]
                    if delivery_date:
                        if type(delivery_date) is float:
                            delivery_date = datetime(
                                *xlrd.xldate_as_tuple(delivery_date, workbook.datemode)
                            )
                        else:
                            delivery_date_str = str(delivery_date)
                            try:
                                delivery_date = datetime.strptime(
                                    delivery_date_str, DATE_FORMAT
                                )
                            except Exception:
                                raise exceptions.UserError(_(
                                    "Delivery date should be in 'yy-mm-dd' format in line number %s!", rownum + 1))
                    if not delivery_date:
                        raise UserError(
                            _("Please add date in line number %s ", rownum + 1)
                        )
                    customer_order_ref = data[3]
                    if not customer_order_ref:
                        raise UserError(
                            _(
                                "Please add customer sales order in line number %s ",
                                rownum + 1,
                            )
                        )
                    partner_rec = partner_obj.search(
                        [("name", "=", str(data[4]))], limit=1
                    )
                    if not partner_rec:
                        raise UserError(
                            _("Customer %s not found in system!", str(data[4]))
                        )
                    barcode = data[11]
                    if type(barcode) is float:
                        barcode = int(barcode)
                    product_rec = product_obj.search(
                        [("barcode", "=", str(barcode))], limit=1
                    )
                    if not product_rec:
                        raise UserError(
                            _(
                                "Product isbn number %s not found in system!",
                                str(barcode),
                            )
                        )
                    analytic_account_rec = analytic_account_obj.search([
                        ("name", "=", str(data[5])),
                        "|",
                        ("company_id", '=', self.env.company.id),
                        ("company_id", '=', False)
                    ], limit=1)
                    product_uom_qty = data[12]
                    if product_uom_qty and type(product_uom_qty) is float:
                        product_uom_qty = product_uom_qty
                    else:
                        product_uom_qty = 0.0
                    price_unit = data[13]
                    if price_unit and type(price_unit) is float:
                        price_unit = price_unit
                    else:
                        price_unit = 0.0
                    # Add as per new requirement : 23/01/2024
                    quotation_qty = data[9]
                    if quotation_qty and type(quotation_qty) is float:
                        quotation_qty = quotation_qty
                    else:
                        quotation_qty = 0.0
                    so_quotation = data[10]
                    if so_quotation and type(so_quotation) is float:
                        so_quotation = so_quotation
                    else:
                        so_quotation = 0.0
                    discount = data[14]
                    # ----------------------------
                    if discount and type(discount) is float:
                        discount = discount
                    else:
                        discount = 0.0
                    if not analytic_account_rec:
                        raise UserError(
                            _("Analytic account %s not found in system!", str(data[5]))
                        )
                    analytic_tag_list = str(data[15]).split(",")
                    analytic_tag_ids = []
                    for analytic_tag in analytic_tag_list:
                        analytic_tag = analytic_tag.strip()
                        analytic_tag_rec = analytic_tag_obj.search(
                            [("name", "=", analytic_tag)], limit=1
                        )
                        if not analytic_tag_rec:
                            raise UserError(
                                _("Analytic tags %s not found in system!", analytic_tag)
                            )
                        analytic_tag_ids.append(analytic_tag_rec.id)
                    if self.is_use_marketplace_values:
                        if str(customer_order_ref) not in so_dict_res:
                            so_dict_res[str(customer_order_ref)] = {
                                "partner_id": partner_rec.id,
                                "customer_so_date": create_date,
                                "commitment_date" : delivery_date,
                                "customer_sales_order": str(customer_order_ref) or "",
                                "analytic_account_id": analytic_account_rec.id,
                                "order_line": [
                                    (
                                        0,
                                        0,
                                        {
                                            "so_qty": quotation_qty, # Add as per new requirement : 23/01/2024
                                            "so_quantity": so_quotation, # Add as per new requirement : 23/01/2024
                                            "product_id": product_rec.id,
                                            "product_uom_qty": product_uom_qty,
                                            "price_unit": price_unit,
                                            "discount": discount,
                                            "analytic_tag_ids": analytic_tag_ids,
                                            "course_id": str(data[16] or ''),
                                            "crn": str(data[17] or ''),
                                            'csn_no': str(data[18] or ''),
                                        },
                                    )
                                ],
                            }
                        else:
                            so_dict_res[str(customer_order_ref)]["order_line"] += [
                                (
                                    0,
                                    0,
                                    {
                                        "so_qty": quotation_qty, # Add as per new requirement : 23/01/2024
                                        "so_quantity": so_quotation, # Add as per new requirement : 23/01/2024
                                        "product_id": product_rec.id,
                                        "product_uom_qty": product_uom_qty,
                                        "price_unit": price_unit,
                                        "discount": discount,
                                        "analytic_tag_ids": analytic_tag_ids,
                                        "course_id": str(data[16] or ''),
                                        "crn": str(data[17] or ''),
                                        'csn_no': str(data[18] or ''),
                                    },
                                )
                            ]
                    else:
                        # Add MCO, SCO and OCO base on excel file data.
                        marketplace_cost = data[6]
                        if marketplace_cost and type(marketplace_cost) is float:
                            marketplace_cost = marketplace_cost
                        else:
                            marketplace_cost = 0.0
                        shipping_cost = data[7]
                        if shipping_cost and type(shipping_cost) is float:
                            shipping_cost = shipping_cost
                        else:
                            shipping_cost = 0.0
                        other_cost = data[8]
                        if other_cost and type(other_cost) is float:
                            other_cost = other_cost
                        else:
                            other_cost = 0.0
                        if str(customer_order_ref) not in so_dict_res:
                            so_dict_res[str(customer_order_ref)] = {
                                "partner_id": partner_rec.id,
                                "customer_so_date": create_date,
                                "commitment_date" : delivery_date,
                                "customer_sales_order": str(customer_order_ref) or "",
                                "analytic_account_id": analytic_account_rec.id,
                                "order_line": [
                                    (
                                        0,
                                        0,
                                        {
                                            "so_qty": quotation_qty, # Add as per new requirement : 23/01/2024
                                            "so_quantity": so_quotation, # Add as per new requirement : 23/01/2024
                                            "product_id": product_rec.id,
                                            "product_uom_qty": product_uom_qty,
                                            "price_unit": price_unit,
                                            "discount": discount,
                                            "marketplace_cost": marketplace_cost,
                                            "shipping_cost": shipping_cost,
                                            "other_cost": other_cost,
                                            "is_compute_cost_from_sheet": True,
                                            "analytic_tag_ids": analytic_tag_ids,
                                            "course_id": str(data[16] or ''),
                                            "crn": str(data[17] or ''),
                                            'csn_no': str(data[18] or ''),
                                        },
                                    )
                                ],
                            }
                        else:
                            so_dict_res[str(customer_order_ref)]["order_line"] += [
                                (
                                    0,
                                    0,
                                    {
                                        "so_qty": quotation_qty, # Add as per new requirement : 23/01/2024
                                        "so_quantity": so_quotation, # Add as per new requirement : 23/01/2024
                                        "product_id": product_rec.id,
                                        "product_uom_qty": product_uom_qty,
                                        "price_unit": price_unit,
                                        "discount": discount,
                                        "marketplace_cost": marketplace_cost,
                                        "shipping_cost": shipping_cost,
                                        "other_cost": other_cost,
                                        "is_compute_cost_from_sheet": True,
                                        "analytic_tag_ids": analytic_tag_ids,
                                        "course_id": str(data[16] or ''),
                                        "crn": str(data[17] or ''),
                                        'csn_no': str(data[18] or ''),
                                    },
                                )
                            ]
                except IOError:
                    pass
        so_list_res = list(so_dict_res.values())
        partner_obj = self.env["res.partner"]

        for rec in so_list_res:
            # Create SO base on excel file data.

            partner_id = rec.get("partner_id")
            if partner_id:
                partner = partner_obj.browse(partner_id)
                division_type_id = partner.division_type_id.id if partner.division_type_id else False
                sale_rec = sale_obj.create(
                    {
                        "partner_id": partner_id,
                        "customer_so_date": rec.get("customer_so_date"),
                        "commitment_date" : rec.get("commitment_date"),
                        "is_imported": True,
                        "analytic_account_id": rec.get("analytic_account_id"),
                        "customer_sales_order": rec.get("customer_sales_order"),
                        "order_line": rec.get("order_line"),
                        "division_type_id": division_type_id,
                    }
                )
                sale_rec.order_line._onchange_uom_qty_discount_price_unit()
        # reload page after import sale order.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
