# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
# ////////////////////////////////////////////////////////////////////////////////////////
# Not Required now : Commented on request of client
# ////////////////////////////////////////////////////////////////////////////////////////

# from odoo import _, api, fields, models
# from odoo.exceptions import UserError

# class StockPickingBatch(models.Model):
#     _inherit = "stock.picking.batch"

#     purchase_order_ids = fields.Many2many("purchase.order")

#     def action_confirm(self):
#         picking_line_list = self.picking_ids.filtered(
#                 lambda r: r.picking_type_id.code == 'incoming').ids
#         purchase_picking_list = (self.purchase_order_ids.mapped(
#             'picking_ids').filtered(
#                 lambda r: r.picking_type_id.code == 'incoming')).ids
#         check =  all(item in purchase_picking_list for item in picking_line_list)

#         if not check:
#             raise UserError(_('Purchase Order and pickings are not matching !'))
#         return super(StockPickingBatch, self).action_confirm()

#     @api.onchange("purchase_order_ids")
#     def _onchange_purchase_order_ids(self):
#         if self.purchase_order_ids:
#             pick_in = self.env["stock.picking.type"].search(
#                 [("company_id", "=", self.env.company.id), ("code", "=", "incoming")],
#                 limit=1,
#             )
#             self.picking_type_id = pick_in.id or False
