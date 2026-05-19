# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import _, api, fields, models
from itertools import groupby
from odoo.tools.float_utils import float_is_zero
from odoo.exceptions import ValidationError, UserError

class ProductProduct(models.Model):
    _inherit = "product.product"

    # @api.model
    # # Get only service type product for service quotation
    # def _search(self,args,offset=0,limit=None,order=None,**kwargs):
    #     args = args or []
    #     context = dict(self._context) or {}
    #     if context.get("is_service_quotation"):
    #         args.extend(
    #             [('detailed_type', '=', 'service')]
    #         )
    #     return super(ProductProduct, self)._search(args,offset=offset,limit=limit,order=order,**kwargs)

    @api.onchange('order_line','order_line.related_so')
    def _onchange_related_so_ref_field(self):
        if self.order_line.filtered(lambda l: not l.related_so and l.product_id.sale_ok): # related SO mandatory for 'Can be sold' enabled products only
            # self.related_so = None
            return {'warning': {
                'title': 'Warning!',
                'message': 'Related SO Required!',
                'type': 'danger',  # You can also use 'danger' for an error message
            }}

# class StockPicking(models.Model):
#     _inherit = "stock.picking"
#
#     def button_validate(self):
#         if self.purchase_id and self.picking_type_id.code == 'incoming' and self.picking_type_id.default_location_dest_id.usage != 'transit' and not self.picking_type_id.default_location_dest_id.is_shipper_location:
#             if not self.purchase_id.mapped('order_line.invoice_lines.move_id').filtered(lambda l: l.state == 'posted'):
#                 raise UserError(_('Please confirm the Bill before validate the Receipt.'))
#             else:
#                 res = super(StockPicking, self).button_validate()
#                 return res
#         else:
#             res = super(StockPicking, self).button_validate()
#             return res
