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


class ImportSaleReturnWizard(models.TransientModel):
    _name = "import.sale.rma.return.wizard"

    file = fields.Binary(string="Select File", help="Add excel file")
    sample_file = fields.Binary("Download File")
    file_name = fields.Char(string="File Name")

    def download_sample_file(self):
        """
            Method to download sample file.
        """
        name_of_file = "sample_sale_rma_return_import.xls"
        fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xls")
        path_list = list(os.path.split(fp.name))
        path_list[len(path_list) - 1] = name_of_file
        file_path = os.path.join(*path_list)
        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet()
        counter = 0
        field_list_to_import = [
            "Sales Order Date",
            "Customer Sales Order",
            "Customer",
            "Product(isbn)",
            "Ordered Quantity",
            "Delivered Quantity",
            "Return Quantity",
            "List Price",
            "Discount",
            "LCO",
            "MCO",
            "SCO",
            "OCO",
            "TCO"
        ]
        for i in field_list_to_import:
            worksheet.write(0, counter, i)
            counter += 1
        workbook.close()
        export_id = base64.b64encode(open(file_path, "rb+").read())
        self.write({"sample_file": export_id, "file_name": name_of_file})
        return {
            "name": "Import Sale Return",
            "view_mode": "form",
            "res_id": self.id,
            "res_model": "import.sale.rma.return.wizard",
            "view_type": "form",
            "type": "ir.actions.act_window",
            "target": "new",
        }

    def import_sale_return(self):
        """
            Method to import sales RMA return.
        """
        if not self.file:
            raise UserError(_("Please upload file!."))
        sale_obj = self.env["sale.order"]
        rma_ret_obj = self.env["rma.ret.mer.auth"]
        partner_obj = self.env["res.partner"]
        product_obj = self.env["product.product"]
        company = self.env.user.company_id
        # analytic_account_obj = self.env["account.analytic.account"]
        # analytic_tag_obj = self.env["account.analytic.tag"]
        try:
            fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            fp.write(binascii.a2b_base64(self.file))
            fp.seek(0)
            workbook = xlrd.open_workbook(fp.name)
            sheet = workbook.sheet_by_index(0)
        except Exception:
            raise exceptions.UserError(_("Invalid file!"))
        so_return_dict_res = {}
        for rownum in range(sheet.nrows):
            if rownum >= 1:
                data = sheet.row_values(rownum)
                try:
                    create_date = data[0]
                    if create_date:
                        if type(create_date) is float:
                            try:
                                create_date = datetime(
                        *xlrd.xldate_as_tuple(create_date, workbook.datemode)
                    )
                            except Exception:
                                raise exceptions.UserError(_("Please add date in line number 1"))
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
                    customer_order_ref = data[1]
                    if not customer_order_ref:
                        raise UserError(
                            _(
                                "Please add customer sales order in line number %s ",
                                rownum + 1,
                            )
                        )
                    partner_rec = partner_obj.search(
                        [("name", "=", str(data[2]))], limit=1
                    )
                    if not partner_rec:
                        raise UserError(
                            _("Customer %s not found in system!", str(data[2]))
                        )
                    barcode = data[3]
                    if type(barcode) is float:
                        barcode = int(barcode)
                    product_rec = product_obj.search(
                        [("barcode", "=", str(barcode))]
                    )
                    if not product_rec:
                        raise UserError(
                            _(
                                "Product isbn number %s not \
found in system!", str(barcode)
                            )
                        )
                    ordered_qty = data[4]
                    if ordered_qty and type(ordered_qty) is float:
                        ordered_qty = ordered_qty
                    else:
                        ordered_qty = 0.0
                    delivered_qty = data[5]
                    if delivered_qty and type(delivered_qty) is float:
                        delivered_qty = delivered_qty
                    else:
                        delivered_qty = 0.0
                    refund_qty = data[6]
                    if refund_qty and type(refund_qty) is float:
                        refund_qty = refund_qty
                    else:
                        refund_qty = 0.0
                    price_unit = data[7]
                    if price_unit and type(price_unit) is float:
                        price_unit = price_unit
                    else:
                        price_unit = 0.0
                    discount = data[8]
                    if discount and type(discount) is float:
                        discount = discount
                    else:
                        discount = 0.0
                    # if not analytic_account_rec:
                    #     raise UserError(
                    #         _("Analytic account %s not found in system!", str(data[3]))
                    #     )
                    # analytic_tag_list = str(data[11]).split(",")
                    # analytic_tag_ids = []
                    # for analytic_tag in analytic_tag_list:
                    #     analytic_tag = analytic_tag.strip()
                    #     analytic_tag_rec = analytic_tag_obj.search(
                    #         [("name", "=", analytic_tag)], limit=1
                    #     )
                    #     if not analytic_tag_rec:
                    #         raise UserError(
                    #             _("Analytic tags %s not found in system!", analytic_tag)
                    #         )
                    #     analytic_tag_ids.append(analytic_tag_rec.id)

                    # Add MCO, SCO and OCO base on excel file data.
                    landed_cost = data[9]
                    if landed_cost and type(landed_cost) is float:
                        landed_cost = landed_cost
                    else:
                        landed_cost = 0.0
                    marketplace_cost = data[10]
                    if marketplace_cost and type(marketplace_cost) is float:
                        marketplace_cost = marketplace_cost
                    else:
                        marketplace_cost = 0.0
                    shipping_cost = data[11]
                    if shipping_cost and type(shipping_cost) is float:
                        shipping_cost = shipping_cost
                    else:
                        shipping_cost = 0.0
                    other_cost = data[12]
                    if other_cost and type(other_cost) is float:
                        other_cost = other_cost
                    else:
                        other_cost = 0.0
                    subtotal_cost = data[13]
                    if subtotal_cost and type(subtotal_cost) is float:
                        subtotal_cost = subtotal_cost
                    else:
                        subtotal_cost = 0.0
                    so_id = sale_obj.search([
                        ("customer_sales_order", "=", customer_order_ref)
                    ], limit=1)
                    if not so_id:
                        raise UserError(_("No SO found with CSO Reference %s ", customer_order_ref))
                    so_line_rec = so_id.order_line.filtered(
                        lambda l: l.product_id.id == product_rec.id)
                    if len(so_line_rec) > 1:
                        raise UserError(
                            _("Duplicate product found for CSO Reference %s, can not import it, kindly create RMA manually", customer_order_ref)
                        )
                    if not ordered_qty:
                        ordered_qty = so_line_rec.product_uom_qty
                    if not delivered_qty:
                        delivered_qty = so_line_rec.qty_delivered
                    if not price_unit:
                        price_unit = so_line_rec.price_unit
                    if not discount:
                        discount = so_line_rec.discount
                    if not landed_cost:
                        landed_cost = so_line_rec.landed_cost
                    if not subtotal_cost:
                        subtotal_cost = sum(
                            [landed_cost, marketplace_cost, shipping_cost, other_cost])
                    if str(customer_order_ref) not in so_return_dict_res:
                        so_return_dict_res[str(customer_order_ref)] = {
                            "partner_id": partner_rec.id,
                            "rma_date": create_date,
                            "sale_order_id": so_id and so_id.id,
                            "rma_sale_lines_ids": [
                                (
                                    0,
                                    0,
                                    {
                                        "product_id": product_rec.id,
                                        "order_quantity": ordered_qty,
                                        "delivered_quantity": delivered_qty,
                                        "refund_qty": refund_qty,
                                        "price_unit": price_unit,
                                        "discount": discount,
                                        "landed_cost": landed_cost,
                                        "marketplace_cost": marketplace_cost,
                                        "shipping_cost": shipping_cost,
                                        "other_cost": other_cost,
                                        "subtotal_cost": subtotal_cost,
                                        "source_location_id": so_id.company_id and so_id.company_id.source_location_id.id or False,
                                        "destination_location_id": so_id.company_id and so_id.company_id.destination_location_id.id or False,
                                        "analytic_account_id": so_id.partner_id.analytic_account_id.id or False,
                                    },
                                )
                            ],
                        }
                    else:
                        so_return_dict_res[str(customer_order_ref)]["rma_sale_lines_ids"] += [
                            (
                                0,
                                0,
                                {
                                    "product_id": product_rec.id,
                                    "order_quantity": ordered_qty,
                                    "delivered_quantity": delivered_qty,
                                    "refund_qty": refund_qty,
                                    "price_unit": price_unit,
                                    "discount": discount,
                                    "landed_cost": landed_cost,
                                    "marketplace_cost": marketplace_cost,
                                    "shipping_cost": shipping_cost,
                                    "other_cost": other_cost,
                                    "subtotal_cost": subtotal_cost,
                                    "source_location_id": so_id.company_id and so_id.company_id.source_location_id.id or False,
                                    "destination_location_id": so_id.company_id and so_id.company_id.destination_location_id.id or False,
                                    "analytic_account_id": so_id.partner_id.analytic_account_id.id or False,
                                },
                            )
                        ]
                except IOError:
                    pass
        so_list_res = list(so_return_dict_res.values())
        for rec in so_list_res:
            # Create SO base on excel file data.
            rma_rec = rma_ret_obj.create(
                {
                    "rma_type": "customer",
                    "rma_date": rec.get("rma_date"),
                    "sale_order_id": rec.get("sale_order_id"),
                    "partner_id": rec.get("partner_id"),
                    "is_imported": True,
                    "rma_sale_lines_ids": rec.get("rma_sale_lines_ids"),
                }
            )
            rma_rec._onchange_partners()
            rma_rec._onchange_sale_purchase_type()
        # reload page after import sale order.
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
