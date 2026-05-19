# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.stock_barcode.controllers.stock_barcode import StockBarcodeController


class StockBarcodePickingBatchController(StockBarcodeController):

    @http.route()
    def save_barcode_data(self, model, res_id, write_field, write_vals):
        # Override this method to set barcode scanned name in picking.
        if res_id:
            picking_rec = request.env[model].sudo().browse(res_id)
            picking_rec.message_post(
                body="Processed the Barcode of this Transfer")
        return super().save_barcode_data(model, res_id, write_field, write_vals)
