# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
##############################################################################


from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _prepare_supplier_info(self, partner, line, price, currency):
        vals = super()._prepare_supplier_info(partner, line, price, currency)
        vals["discount"] = line.po_discount if line.po_list_price else line.discount
        return vals

    # def _add_supplier_to_product(self):
    #     """Insert a mapping of products to PO lines to be picked up
    #     in supplierinfo's create()"""
    #     self.ensure_one()
    #     po_line_map = {
    #         line.product_id.product_tmpl_id.id: line for line in self.order_line
    #     }
    #     return super(
    #         PurchaseOrder, self.with_context(po_line_map=po_line_map)
    #     )._add_supplier_to_product()
