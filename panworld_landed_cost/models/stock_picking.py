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
from odoo.exceptions import ValidationError
from odoo.tests.common import Form
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    landed_cost_count = fields.Integer(compute="_compute_landed_cost_count")
    grn_tracking = fields.Char(string="Tracking(AWB)")
    grn_tracking_number_id = fields.Many2one(
        "tracking.number", 
        string='Tracking Number',
        compute='_compute_grn_tracking_number_id',
        store=True,
        readonly=False
    )
    different_shipment = fields.Boolean(string="Different Shipment")

    total_demand_qty = fields.Float(
        string="Total Demand Qty", compute="_compute_total_quantity", store=True
    )
    total_counted_qty = fields.Float(
        string="Total Counted Qty", readonly=True, compute="_compute_total_counted_quantity", store=True
    )

    total_done_qty = fields.Float(
        string="Total Done Qty",
        compute="_compute_total_done_qty",
        store=True,
    )

    @api.depends('move_ids.product_uom_qty')
    def _compute_total_quantity(self):
        for rec in self:
            rec.total_demand_qty = sum(m.product_uom_qty for m in rec.move_ids)

    @api.depends('move_line_ids.quantity')
    def _compute_total_counted_quantity(self):
        for rec in self:
            rec.total_counted_qty = sum(ml.quantity for ml in rec.move_line_ids)

    @api.depends('move_line_ids.quantity', 'move_line_ids.picked')
    def _compute_total_done_qty(self):
        for rec in self:
            # In Odoo 19, 'quantity' on move lines is only 'Done' if 'picked' is True
            rec.total_done_qty = sum(ml.quantity for ml in rec.move_line_ids if ml.picked)
    ship_no = fields.Char(string='Ship No.', compute='_compute_tracking_details', store=True)
    boe_no = fields.Char(string='BOE No.', compute='_compute_tracking_details', store=True)
    boe_date = fields.Date(string='BOE Date', compute='_compute_tracking_details', store=True)
    ready_for_scan_1 = fields.Char(string="Ready for Scan", compute='_compute_tracking_details', store=True)
    grn_tracking_number_value = fields.Char(string="Tracking Number", compute='_compute_tracking_details', store=True)
    consolidated_weight_shipping = fields.Float(string="Consolidation Weight", compute='_compute_tracking_details', store=True)

    @api.depends('partner_bill_id', 'different_shipment')
    def _compute_grn_tracking_number_id(self):
        for picking in self:
            if picking.partner_bill_id and not picking.different_shipment:
                picking.grn_tracking_number_id = picking.partner_bill_id.tracking_number_bill_id
            # Note: We don't force it to False if different_shipment is True
            # to allow manual selection, but we ensure it stays False if no bill.
            elif not picking.partner_bill_id:
                picking.grn_tracking_number_id = False

    @api.depends('grn_tracking_number_id', 'grn_tracking_number_id.ship_no')
    def _compute_tracking_details(self):
        for picking in self:
            source = False
            if (picking.partner_bill_id and picking.partner_bill_id.tracking_number_bill_id and
                    not picking.different_shipment and
                    picking.partner_bill_id.tracking_number_bill_id != picking.grn_tracking_number_id):
                source = picking.partner_bill_id.tracking_number_bill_id
            else:
                source = picking.grn_tracking_number_id
            if source:
                picking.grn_tracking_number_value = source.name
                picking.ship_no = source.ship_no
                picking.boe_no = source.boe_no
                picking.boe_date = source.boe_date
                picking.ready_for_scan_1 = source.ready_to_scan
                picking.consolidated_weight_shipping = source.consolidated_weight
            else:
                picking.grn_tracking_number_value = False
                picking.ship_no = False
                picking.boe_no = False
                picking.boe_date = False
                picking.ready_for_scan_1 = False
                picking.consolidated_weight_shipping = 0.0

    @api.onchange("partner_id")
    def _onchange_partner(self):
        for rec in self:
            context = dict(self.env.context)
            rec.picking_type_id = False
            rec.carrier_id = False
            if context.get("is_action_multi_grn"):
                picking_type_rec = self.env["stock.picking.type"].search([
                    ("is_consolidated_picking", "=", True),
                    ("company_id", '=', self.env.company.id)
                ], limit=1)
                rec.picking_type_id = picking_type_rec.id

    @api.onchange("purchase_ids")
    def _onchange_purchase_ids(self):
        po_list = self.purchase_ids.mapped("name")
        purchase_orders = self.purchase_ids._origin
        grn_tracking_list = (
            purchase_orders.mapped("picking_ids")
            .filtered(lambda l: l.state == "done" and l.grn_tracking)
            .mapped("grn_tracking")
        )
        customer_sales_order_list = self.purchase_ids.filtered(
            lambda p: p.customer_sales_order
        ).mapped("customer_sales_order")
        self.update(
            {
                "origin": po_list and ", ".join(po_list) or False,
                "carrier_tracking_ref": grn_tracking_list
                and ", ".join(list(set(grn_tracking_list)))
                or False,
                "customer_sales_order": customer_sales_order_list
                and ", ".join(customer_sales_order_list)
                or False,
                "carrier_id": purchase_orders
                and purchase_orders[0].carrier_id.id
                or False,
            }
        )
        return super()._onchange_purchase_ids()

    def _prepare_landed_cost_vals(self, additional_po_service_lines):
        consolidated_list = []

        # Optimization: Group lines by product ID first to avoid repeated filtering
        lines_by_product = {}
        for line in additional_po_service_lines:
            lines_by_product.setdefault(line.product_id, []).append(line)

        for product, lines in lines_by_product.items():
            first_line = lines[0]
            po_currency = first_line.currency_id
            company_currency = self.company_id.currency_id or self.env.company.currency_id
            consolidated_cost = sum(l.consolidated_price for l in lines)

            # Convert consolidated cost to company currency
            price_unit_company_curr = po_currency._convert(
                consolidated_cost, company_currency, self.company_id or self.env.company,
                self.scheduled_date or fields.Date.today()
            )

            consolidated_list.append({
                "product_id": product.id,
                "name": first_line.name,
                "split_method": product.split_method_landed_cost,
                "price_unit": price_unit_company_curr,
                "consolidated_cost": price_unit_company_curr,
            })

        # Prepare cost lines data
        cost_lines = []
        for line in consolidated_list:
            if not line.get("split_method"):
                raise ValidationError(
                    _("Please define split method in delivery product")
                )

            cost_line_vals = {
                'product_id': line.get("product_id"),
                'name': line.get("name"),
                'split_method': line.get("split_method"),
                'price_unit': line.get("price_unit"),
                'consolidated_cost': line.get("consolidated_cost"),
            }
            cost_lines.append((0, 0, cost_line_vals))

        # Create landed cost directly
        landed_cost_vals = {
            'cost_lines': cost_lines,
            'date': self.scheduled_date,
        }

        landed_cost = self.env["stock.landed.cost"].create(landed_cost_vals)
        return landed_cost

    def create_landed_cost(self):
        landed_costs = self.env["stock.landed.cost"]
        pick_ids = self.filtered(lambda l: l.picking_type_id.code == "incoming")
        for rec in pick_ids:
            po_service_lines = rec.purchase_ids.mapped("additional_po_service_ids")
            landed_cost = rec._prepare_landed_cost_vals(po_service_lines)
            if landed_cost:
                landed_cost.write(
                    {
                        "picking_ids": [(6, 0, [rec.id])],
                        "weight": rec.weight,
                        "consolidated_weight": rec.consolidated_weight,
                        "consolidated_weight": rec.consolidated_weight_shipping,
                        "carrier_tracking_ref": rec.carrier_tracking_ref,
                        "delivery_carrier_id": rec.carrier_id.id,
                        "done_quantity": rec.total_done_qty,
                        'grn_tracking_number_id': rec.grn_tracking_number_id.id,
                        'related_bill': [(6, 0, [rec.partner_bill_id.id])] if rec.partner_bill_id else False
                    }
                )
                landed_cost.compute_landed_cost()
                landed_costs |= landed_cost
        return landed_costs

    def button_validate(self):
        start_time = datetime.now()
        _logger.info(">>> PERFORMANCE: panworld_landed_cost button_validate START for picking %s (ID: %s)", self.mapped('name'), self.ids)
        landed_cost = self.env["stock.landed.cost"]
        pickings_to_update = self.filtered(lambda p: p.purchase_id and p.picking_type_id.code in ['incoming', 'internal'])
        if pickings_to_update:
            pickings_to_update.write({'scheduled_date': datetime.now()})

        super_start = datetime.now()
        res = super(StockPicking, self.with_context(bypass_presale_track_block=True)).button_validate()
        _logger.info(">>> PERFORMANCE: panworld_landed_cost button_validate SUPER() took %s for picking %s (ID: %s)", datetime.now() - super_start, self.mapped('name'), self.ids)

        # if self.picking_type_id.warehouse_id.code != 'UKWAR':
        lc_ids = landed_cost.search([("picking_ids", "in", self.ids)])
        if lc_ids:
            action = self.env["ir.actions.actions"]._for_xml_id(
                "stock_landed_costs.action_stock_landed_cost"
            )
            action["domain"] = [("id", "in", lc_ids.ids)]
            if len(lc_ids.ids) > 1:
                action["views"] = ([[self.env.ref("stock_landed_costs.view_stock_landed_cost_tree").id,"list",],
                        [self.env.ref("stock_landed_costs.view_stock_landed_cost_form").id,"form",],],)
            elif len(lc_ids.ids) == 1:
                action["views"] = ([self.env.ref("stock_landed_costs.view_stock_landed_cost_form").id, "form",],)
                action["res_id"] = lc_ids.ids[0]
            else:
                action = {"type": "ir.actions.act_window_close"}
            _logger.info(">>> PERFORMANCE: panworld_landed_cost button_validate TOTAL took %s for picking %s (ID: %s)", datetime.now() - start_time, self.mapped('name'), self.ids)
        return res

    def action_view_landed_cost(self, landed_costs=None):
        # if self.env.user.has_group("panworld_uk_warehouse.group_uk_warehouse_user_uk"):
        #     raise ValidationError (_("You Don't have access to view landed cost!"))
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock_landed_costs.action_stock_landed_cost"
        )
        lc_view_id = self.env.ref("stock_landed_costs.view_stock_landed_cost_form")
        lc_ids = False
        if landed_costs:
            lc_ids = landed_costs
        else:
            lc_ids = self.env["stock.landed.cost"].search(
                [("picking_ids", "in", self.ids)]
            )
        if len(lc_ids.ids) > 1:
            action["domain"] = [("picking_ids", "in", self.ids)]
        elif len(lc_ids.ids) == 1:
            action["views"] = [(lc_view_id.id, "form")]
            action["res_id"] = lc_ids[0].id
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action

    def _compute_landed_cost_count(self):
        picking_data = {rec.id: 0 for rec in self}
        landed_costs = self.env["stock.landed.cost"].search([("picking_ids", "in", self.ids)])
        for lc in landed_costs:
            for picking in lc.picking_ids:
                if picking.id in picking_data:
                    picking_data[picking.id] += 1

        for rec in self:
            rec.landed_cost_count = picking_data.get(rec.id, 0)

    def action_assign(self):
        """ Performance optimization: bypass expensive putaway and pack checks for large pickings.
            Also pre-builds quants cache for ALL MTS moves to eliminate per-move DB queries.
            Also skips per-move orderpoint updates (runs once at end instead of N times).
        """
        start_time = datetime.now()
        move_count = len(self.move_ids)
        _logger.info(">>> PERFORMANCE: panworld_landed_cost action_assign START for picking %s (ID: %s) (moves: %s)", self.mapped('name'), self.ids, move_count)

        if move_count > 500:
            _logger.info(">>> PERFORMANCE: Large picking detected (%s moves) for picking %s (ID: %s) - applying all optimizations", move_count, self.mapped('name'), self.ids)

            # Pre-build quants cache for ALL moves (not just MTO like Odoo does by default).
            # This means the reservation loop does ONE big DB query instead of N individual ones.
            all_moves = self.move_ids.filtered(
                lambda m: not m.picked and m.state in ['confirmed', 'waiting', 'partially_available']
                and not m._should_bypass_reservation()
            )
            quants_cache = self.env['stock.quant']._get_quants_by_products_locations(
                all_moves.product_id, all_moves.location_id
            )
            _logger.info(">>> PERFORMANCE: quants_cache built for %s products/locations for picking %s (ID: %s)", len(quants_cache), self.mapped('name'), self.ids)

            # `avoid_putaway_rules` is the CORRECT Odoo 19 context key to skip _apply_putaway_strategy
            # `bypass_entire_pack` skips _check_entire_pack (used in both core + our custom _action_assign)
            # `skip_orderpoint_update` prevents orderpoint updates being called per move write
            res = super(StockPicking, self.with_context(
                bypass_entire_pack=True,
                avoid_putaway_rules=True,
                quants_cache=quants_cache,
                skip_orderpoint_update=True,
                bulk_create_move_lines=True,
            )).action_assign()

            # Run orderpoint update ONCE for all affected moves instead of per-move
            _logger.info(">>> PERFORMANCE: Running single batch _update_orderpoints for %s moves for picking %s (ID: %s)", len(all_moves), self.mapped('name'), self.ids)
            all_moves.with_context(skip_orderpoint_update=False)._update_orderpoints()
        else:
            res = super(StockPicking, self).action_assign()

        super_time = datetime.now()
        _logger.info(">>> PERFORMANCE: panworld_landed_cost action_assign SUPER() took %s for picking %s (ID: %s)", super_time - start_time, self.mapped('name'), self.ids)

        for picking in self:
            moves_to_update = picking.move_ids.filtered(lambda m: m.picked)
            if moves_to_update:
                _logger.info(">>> PERFORMANCE: action_assign resetting 'picked' flag for %s moves in picking %s", len(moves_to_update), picking.id)
                moves_to_update.write({'picked': False})

        _logger.info(">>> PERFORMANCE: panworld_landed_cost action_assign TOTAL took %s for picking %s (ID: %s)", datetime.now() - start_time, self.mapped('name'), self.ids)
        return res

    def _action_done(self):
        start_time = datetime.now()
        _logger.info(">>> PERFORMANCE: panworld_landed_cost _action_done START for picking %s (ID: %s)", self.mapped('name'), self.ids)

        super_start = datetime.now()
        res = super(StockPicking, self.with_context(bypass_presale_track_block=True))._action_done()
        _logger.info(">>> PERFORMANCE: panworld_landed_cost _action_done SUPER() DONE in %s for picking %s (ID: %s)", datetime.now() - super_start, self.mapped('name'), self.ids)

        update_start = datetime.now()
        for picking in self:
            # For multi-step process: ensure the next transfer (e.g. Store) starts with 0 Done Qty
            next_moves = picking.move_ids.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel'))
            if next_moves:
                next_moves.write({'picked': False})
                next_pickings = next_moves.mapped('picking_id')
                next_pickings.move_line_ids.write({'picked': False})
        _logger.info(">>> PERFORMANCE: panworld_landed_cost _action_done NEXT MOVES update took %s for picking %s (ID: %s)", datetime.now() - update_start, self.mapped('name'), self.ids)

        # flag = False
        # if self.env.context.get('active_model') == 'purchase.order' or self.env.context.get("is_action_multi_grn"):
        #     flag = True
        # elif self and self.purchase_ids:
        #     flag = True
        # if flag:
        #     lc_create_start = datetime.now()
        #     landed_costs = self.create_landed_cost()
        #     _logger.info(">>> PERFORMANCE: create_landed_cost took %s", datetime.now() - lc_create_start)
        #     self.action_view_landed_cost(landed_costs)

        _logger.info(">>> PERFORMANCE: panworld_landed_cost _action_done TOTAL took %s for picking %s (ID: %s)", datetime.now() - start_time, self.mapped('name'), self.ids)
        return res
