# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import datetime
import logging
_logger = logging.getLogger(__name__)

READONLY_STATES = {
    "assigned": [("readonly", True)],
    "done": [("readonly", True)],
    "cancel": [("readonly", True)],
}


class StockPicking(models.Model):
    _inherit = "stock.picking"

    purchase_ids = fields.Many2many(
        "purchase.order", string="Purchase Order", states=READONLY_STATES
    )
    is_consolidated_picking = fields.Boolean(
        related="picking_type_id.is_consolidated_picking", string="Consolidated Picking"
    )
    is_imported = fields.Boolean(
        string="Is imported?", help="Import transfer from sheet", copy=False)
    shipper_stock_added = fields.Char()
    picking_sequence_code = fields.Char( related="picking_type_id.sequence_code", readonly="True")


    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        for rec in self:
            rec.purchase_ids = False

    @api.onchange("purchase_ids")
    def _onchange_purchase_ids(self):
        for rec in self:
            rec.move_ids = [(5,)]
            rec.shipper_stock_added = ""
            move_list = []
            vals = {}
            added_grn= []
            shipper_stock_str = ""
            total_stock_picking = self.env['stock.picking']
            for purchase_order in rec.purchase_ids:
                grn_pickings = purchase_order._origin.picking_ids.filtered(
                    lambda l: l.picking_type_id.is_consolidated_picking == True
                )
                for grn in grn_pickings:
                    added_grn.append(grn.shipper_stock_added)

            for purchase_order in rec.purchase_ids:
                stock_picking = purchase_order._origin.picking_ids.filtered(
                    lambda l: l.state == "done" and l.picking_type_id.is_consolidated_picking == False and l.name not in added_grn
                )
                total_stock_picking |= stock_picking
                stock_moves = stock_picking.mapped("move_ids")
                for move in stock_moves:
                    vals = {
                        "product_id": move.product_id.id,
                        "purchase_order_id": purchase_order._origin.id,
                        "location_id": rec.location_id.id,
                        "weight": move.weight,
                        "description_picking": move.description_picking,
                        "product_uom_id": move.product_uom_id.id,
                        "product_uom_qty": move.product_uom_qty,
                        "date": move.date,
                        "date_deadline": move.date_deadline,
                        "location_dest_id": rec.location_dest_id.id,
                        "purchase_line_id": move.purchase_line_id.id,
                    }
                    move_list.append((0, 0, vals))
            if total_stock_picking:
                if len(total_stock_picking) ==1:
                    shipper_stock_str = total_stock_picking.name
                else:
                    shipper_stock_str = ",".join(total_stock_picking.mapped('name'))
                # added_pikings
            rec.update({'shipper_stock_added': shipper_stock_str})
            rec.move_line_ids = move_list

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, **kwargs):
        domain = domain or []
        context = self.env.context or {}
        if context.get("is_action_multi_grn"):
            domain.extend([("picking_type_id.is_consolidated_picking", "=", True)])

        # Hide 'waiting' state for purchase-related transfers as requested
        is_purchase_view = context.get('is_action_multi_grn') or context.get('search_default_purchase_id') or context.get('default_purchase_id')
        if is_purchase_view:
            domain.append(('state', '!=', 'waiting'))

        return super(StockPicking, self)._search(
            domain,
            offset=offset,
            limit=limit,
            order=order,
        )

    # def button_validate(self):
    #     res = super().button_validate()
    #     if self.env.context.get('skip_backorder'):
    #        for move_ids_wp in self.move_ids:
    #             if move_ids_wp.quantity == 0 and not move_ids_wp.cancel_reason:
    #                 data = self.move_ids.filtered(
    #                     lambda l: l.product_id.id == move_ids_wp.product_id.id and l.cancel_reason and l.quantity !=0)
    #                 if len(data) > 1:
    #                     move_ids_wp.cancel_reason = data.cancel_reason[0]
    #                 else:
    #                     move_ids_wp.cancel_reason = data.cancel_reason
    #     for rec in self:
    #         if rec.picking_sequence_code == 'SHIP' and rec.state in ['done']:
    #             picking_type_id = self.env['stock.picking.type'].search(
    #                 [('company_id', '=', rec.company_id.id), ('default_location_src_id.usage', '=', 'transit'),
    #                  ('default_location_src_id.is_shipper_location', '=', True)], limit=1)
    #             if picking_type_id:
    #                 grn_values_dict = {
    #                     'partner_id': rec.partner_id.id,
    #                     'shipper_stock_added': rec.name,
    #                     'picking_type_id': picking_type_id.id,
    #                     'origin': rec.origin,
    #                     'location_id': picking_type_id.default_location_src_id.id,
    #                     'location_dest_id': picking_type_id.default_location_dest_id.id,
    #                     'move_type': 'direct',
    #                     'state': 'draft',
    #                     'partner_bill_id': rec.partner_bill_id.id if rec.partner_bill_id else False,
    #                     'carrier_id': rec.carrier_id.id if rec.carrier_id else False,
    #                     'purchase_ids': [(4, rec.purchase_id.id)] if rec.purchase_id else False,
    #                 }
    #                 grn_picking_id = self.env['stock.picking'].create(grn_values_dict)
    #                 new_move_lines = self.env['stock.move']
    #                 for line in rec.move_ids:
    #                     new_move_lines += line.copy()
    #                 new_move_lines.picking_id = self.env['stock.picking']
    #                 new_move_lines.picking_id = grn_picking_id
    #                 new_move_lines.purchase_order_id = rec.purchase_id
    #                 new_move_lines.location_id = grn_picking_id.location_id
    #                 new_move_lines.location_dest_id = grn_picking_id.location_dest_id
    #                 grn_picking_id.move_ids = [(6, 0, new_move_lines.ids)]
    #     return res

    def button_validate(self):
        start_time = datetime.datetime.now()
        _logger.info(">>> PERFORMANCE: button_validate START for picking %s (ID: %s)", self.mapped('name'), self.ids)

        for picking in self:
            if picking.picking_type_id.code == 'outgoing':
                for move in picking.move_ids:
                    if move.product_uom_qty < move.quantity:
                        product_ref = move.product_id.default_code or move.product_id.display_name
                        raise ValidationError(_("Delivered quantity (%(delivered)s) cannot be greater than the demand quantity (%(demand)s) for product %(product_ref)s.") % {
                            'delivered': move.quantity,
                            'demand': move.product_uom_qty,
                            'product_ref': product_ref,
                        })

        super_start = datetime.datetime.now()
        res = super(StockPicking, self.with_context(bypass_presale_track_block=True)).button_validate()
        _logger.info(">>> PERFORMANCE: button_validate SUPER() took %s for picking %s (ID: %s)", datetime.datetime.now() - super_start, self.mapped('name'), self.ids)


        # First section: Handle skip_backorder context
        if self.env.context.get('skip_backorder'):
            for move in self.move_ids:
                if move.quantity == 0 and not move.cancel_reason:
                    data = self.move_ids.filtered(
                        lambda m: m.product_id == move.product_id and
                                  m.cancel_reason and m.quantity != 0
                    )
                    if data:
                        move.cancel_reason = data[0].cancel_reason

        # Second section: Create GRN for SHIP pickings
        ship_pickings = self.filtered(
            lambda p: p.picking_sequence_code == 'SHIP' and p.state == 'done'
        )

        if ship_pickings:
            grn_start = datetime.datetime.now()
            grns_to_process = self.env['stock.picking']
            for picking in ship_pickings:
                picking_type_id = self.env['stock.picking.type'].search([
                    ('company_id', '=', picking.company_id.id),
                    ('default_location_src_id.usage', '=', 'transit'),
                    ('default_location_src_id.is_shipper_location', '=', True)
                ], limit=1)

                if picking_type_id:
                    # Faster than copy_data: prepare vals manually
                    move_lines_data = []
                    for line in picking.move_ids:
                        move_lines_data.append((0, 0, {
                            'description_picking': line.description_picking,
                            'product_id': line.product_id.id,
                            'product_uom': line.product_uom.id,
                            'product_uom_qty': line.quantity,
                            'quantity': line.quantity,
                            'picked': True,
                            'location_id': picking_type_id.default_location_src_id.id,
                            'location_dest_id': picking_type_id.default_location_dest_id.id,
                            'purchase_line_id': line.purchase_line_id.id,
                            'purchase_order_id': picking.purchase_id.id if picking.purchase_id else False,
                        }))

                    grn_values = {
                        'partner_id': picking.partner_id.id,
                        'shipper_stock_added': picking.name,
                        'picking_type_id': picking_type_id.id,
                        'origin': picking.origin,
                        'location_id': picking_type_id.default_location_src_id.id,
                        'location_dest_id': picking_type_id.default_location_dest_id.id,
                        'move_type': 'direct',
                        'state': 'draft',
                        'partner_bill_id': picking.partner_bill_id.id if picking.partner_bill_id else False,
                        'carrier_id': picking.carrier_id.id if picking.carrier_id else False,
                        'purchase_ids': [(4, picking.purchase_id.id)] if picking.purchase_id else False,
                        'move_ids': move_lines_data,
                    }
                    grns_to_process |= self.env['stock.picking'].create(grn_values)

            if grns_to_process:
                grns_to_process.action_confirm()
                # Batch assignment is much faster than per-record
                grns_to_process.action_assign()
            _logger.info(">>> PERFORMANCE: button_validate SHIP/GRN Logic took %s for picking %s (ID: %s)", datetime.datetime.now() - grn_start, self.mapped('name'), self.ids)

        # Third section: Create Delivery for PICK pickings (Sequential 2-step)
        pick_pickings = self.filtered(
            lambda p: p.state == 'done' and p.sale_id and
                      p.location_dest_id == p.picking_type_id.warehouse_id.wh_output_stock_loc_id
        )
        if pick_pickings:
            for picking in pick_pickings:
                warehouse = picking.picking_type_id.warehouse_id
                # Check if delivery already exists for this SO to avoid duplicates
                existing_delivery = picking.sale_id.picking_ids.filtered(
                    lambda p: p.state not in ('cancel') and p.picking_type_id.code == 'outgoing'
                )
                if not existing_delivery:
                    delivery_type = self.env['stock.picking.type'].search([
                        ('company_id', '=', picking.company_id.id),
                        ('code', '=', 'outgoing'),
                        ('warehouse_id', '=', warehouse.id)
                    ], limit=1)
                    if delivery_type:
                        move_vals = []
                        for move in picking.move_ids:
                            move_vals.append((0, 0, {
                                'description_picking': move.description_picking,
                                'product_id': move.product_id.id,
                                'product_uom_qty': move.quantity,
                                'product_uom': move.product_uom.id,
                                'location_id': warehouse.wh_output_stock_loc_id.id,
                                'location_dest_id': picking.sale_id.partner_shipping_id.property_stock_customer.id,
                                'sale_line_id': move.sale_line_id.id,
                            }))

                        delivery_vals = {
                            'partner_id': picking.partner_id.id,
                            'picking_type_id': delivery_type.id,
                            'location_id': warehouse.wh_output_stock_loc_id.id,
                            'location_dest_id': picking.sale_id.partner_shipping_id.property_stock_customer.id,
                            'origin': picking.origin,
                            'sale_id': picking.sale_id.id,
                            'move_ids': move_vals,
                        }
                        new_delivery = self.env['stock.picking'].create(delivery_vals)
                        new_delivery.action_confirm()

        _logger.info(">>> PERFORMANCE: button_validate TOTAL took %s for picking %s (ID: %s)", datetime.datetime.now() - start_time, self.mapped('name'), self.ids)
        return res

    def _action_done(self):
        res = super(StockPicking, self.with_context(bypass_presale_track_block=True))._action_done()

        # Optimized chained transfer processing for incoming pickings
        incoming_pickings = self.filtered(lambda p: p.picking_type_code == 'incoming')
        if not incoming_pickings:
            return res

        # 1. Identify all relevant destination moves in one pass
        dest_moves = incoming_pickings.move_ids.move_dest_ids.filtered(
            lambda m: m.state not in ('done', 'cancel') and
            m.picking_id and m.picking_id.picking_type_code == 'internal'
        )

        if not dest_moves:
            return res

        # 2. Batch confirm all waiting destination moves
        dest_moves.filtered(lambda m: m.state == 'waiting')._action_confirm()

        # 3. Process quantity updates
        # Optimization: Group moves by quantity to batch write where possible
        qty_groups = {}
        for m in dest_moves:
            qty = m.product_uom_qty
            qty_groups.setdefault(qty, []).append(m.id)

        for qty, ids in qty_groups.items():
            self.env['stock.move'].browse(ids).write({
                'quantity': qty,
                'picked': True
            })

        # 4. Batch assign all affected pickings
        pickings_to_assign = dest_moves.mapped('picking_id')
        if pickings_to_assign:
            # Re-confirm to ensure proper state transition
            pickings_to_assign.filtered(lambda p: p.state == 'waiting').action_confirm()
            pickings_to_assign.action_assign()
        return res

    @api.depends('state', 'move_ids', 'move_ids.state')
    def _compute_show_check_availability(self):
        super()._compute_show_check_availability()
        for picking in self:
            # Hide if it's a direct receipt from PO (not via shipper)
            if picking.purchase_id and picking.purchase_id.shipping_option_id and not picking.purchase_id.shipping_option_id.is_via_shipper:
                picking.show_check_availability = False
                continue

            if picking.picking_type_code == 'internal' and picking.state in ('confirmed', 'assigned'):
                # Hide if it's a GRN picking from SHIP or a chained internal picking from a receipt
                is_from_receipt = any(move.move_orig_ids.filtered(lambda x: x.picking_type_id.code == 'incoming') for move in picking.move_ids)
                if picking.shipper_stock_added or is_from_receipt:
                    picking.show_check_availability = False
