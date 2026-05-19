# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
import logging
from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import UserError,ValidationError
_logger = logging.getLogger(__name__)
# from odoo.exceptions import Warning


class PurchaseOrderCustom(models.Model):
    _inherit = 'purchase.order'

    # def update_to_be_received_qty(self):
    #
    #     for order in self:
    #         for order_line in order.order_line:
    #             # Calculate and update the "To Be Received Qty" as needed
    #             to_be_received_qty = 0
    #             order_line.write({'to_be_received_qty': to_be_received_qty})

    def merge_compare_po(self):
        # Opens wizard on "compare" server action from PO tree view
        if len(set(self.partner_id.ids)) > 1:
            raise UserError(_("Please select PO with same vendor!"))
        else:
            return {
                'name': _("Compare PO Lines Wizard"),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'target': 'new',
                'res_model': 'compare.po.lines.wizard',
                'context': {'active_ids': self.ids,'compare_po':True},
            }

    def create_bill_for_multi_po(self):
        # Opens wizard on "compare" server action from PO tree view
        if len(set(self.partner_id.ids)) > 1:
            raise UserError(_("Please select PO with same vendor!"))
        elif len(set(self.carrier_id.ids)) > 1:
            raise UserError(_("Please select PO with same Delivery method!"))
        for po in self:
            if po.state not in ['purchase', 'done']:
                raise UserError(_("Please Select All PO With Confirm State!"))
        else:
            return {
                'name': _("Create Bill For Multi PO"),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'target': 'new',
                'res_model': 'compare.po.lines.wizard',
                'context': {'active_ids': self.ids,'create_bill':True},
            }


    def _prepare_backorder_picking(self, order):
        # order = self[0]
        if not order.group_id:
            order.group_id = order.group_id.create({
                'name': ",".join(list(set(order.mapped('name')))),
                'partner_id': order.partner_id.id
            })
        if not order.partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s", order.partner_id.name))
        picking_type = order.picking_type_id.filtered(
            lambda p: p.code == 'incoming')  # Select one with Type of Operation = Receipt
        if not picking_type:
            picking_type = order.picking_type_id

        if len(order) == 1:
            location_dest_id = order._get_destination_location(),
        else:
            location_dest_id = picking_type.default_location_dest_id.id

        return {
            'picking_type_id': picking_type[0].id,
            'partner_id': order.partner_id.id,
            'user_id': False,
            'date': order.date_order,
            'origin': ",".join(list(set(order.mapped('name')))),
            'location_dest_id': location_dest_id,
            'location_id': order.partner_id.property_stock_supplier.id,
            'company_id': order.company_id.id,
        }

    def _create_diff_backorder_picking(self, lines_backorder, action_backorder=False):
        if action_backorder:
            StockPicking = self.env['stock.picking']
            # bo_picking = StockPicking
            for order in self:
                # if not bo_picking:
                if any(product.type in ['product', 'consu'] for product in lines_backorder.product_id):
                    order = order.with_company(order.company_id)
                    res = order._prepare_backorder_picking(order)
                    picking = StockPicking.with_user(SUPERUSER_ID).create(res)
                    # bo_picking |= picking
                    moves = lines_backorder.filtered(lambda x: x.order_id.id == order.id).with_context(
                        action_backorder=True)._create_stock_moves(picking)
                    # moves = lines_backorder.with_context(action_backorder=True)._create_stock_moves(picking)
                    # moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                    seq = 0
                    for move in sorted(moves, key=lambda move: move.date):
                        seq += 5
                        move.sequence = seq
                    # moves._action_assign()
                    picking.message_post_with_view('mail.message_origin_link',
                                                   values={'self': picking, 'origin': order},
                                                   subtype_id=self.env.ref('mail.mt_note').id)
                # else:
                #     order.picking_ids += bo_picking

    # def _create_picking(self):
    #     """Override function to create new picking all time"""
    #     StockPicking = self.env['stock.picking']
    #     for order in self.filtered(lambda po: po.state in ('purchase', 'done')):
    #         if any(product.type in ['product', 'consu'] for product in order.order_line.product_id):
    #             order = order.with_company(order.company_id)
    #             res = order._prepare_picking()
    #             picking = StockPicking.with_user(SUPERUSER_ID).create(res)
    #             moves = order.order_line._create_stock_moves(picking)
    #             moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
    #             seq = 0
    #             for move in sorted(moves, key=lambda move: move.date):
    #                 seq += 5
    #                 move.sequence = seq
    #             moves._action_assign()
    #             picking.message_post_with_view('mail.message_origin_link',
    #                                            values={'self': picking, 'origin': order},
    #                                            subtype_id=self.env.ref('mail.mt_note').id)
    #     return True







