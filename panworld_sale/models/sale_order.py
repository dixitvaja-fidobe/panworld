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


class SaleOrder(models.Model):
    _inherit = "sale.order"

    internal_ref_no = fields.Char(string="Internal Ref. No.")
    tat_breach = fields.Boolean(default=False)
    academic_year_id = fields.Many2one('academic.year', string="Academic Year", ondelete="restrict")
    academic_year_name = fields.Char(related='academic_year_id.name', string="Academic Year Name", store=True)
    total_order_quantity = fields.Integer(
        compute="_compute_total_order_quantity", string='Total Order Quantity')

    customer_account = fields.Char('Customer Account')
    presale_original_name = fields.Char(string='Original Sequence', readonly=True, copy=False)
    sales_manager_id = fields.Many2one("hr.employee", string="Sales Manager", copy=False, required=True)
    customer_sales_order = fields.Char(
        string="CSO Reference", help="Customer Sales Order"
    )
    customer_so_date = fields.Date(
        string="CSO Reference Date", help="Customer Sales Order Date"
    )
    total_weight = fields.Float(
        compute="_compute_total_weight",
        string="Total Weight (in g)",
        help="Total weight of all products in sale order lines", store=True
    )
    total_est_sales = fields.Float(
        compute="_compute_total_est_sales",
        string="Total Est. Sales",
        help="Total estimated sales", store=True
    )
    total_est_landed_cost = fields.Float(
        compute="_company_total_est_landed_cost",
        string="Total Est. Landed cost",
        help="Total estimated landed cost", store=True
    )
    total_est_dcost = fields.Float(
        compute="_compute_total_est_dcost",
        string="Total Est. Dcost",
        help="Total estimated Dcost", store=True
    )
    total_cost = fields.Float(
        compute="_compute_total_cost",
        string="Total Cost",
        help="Total cost base on total estimated landed cost and total \
            estimated Dcost", store=True
    )
    gp_percentage = fields.Float(
        compute="_compute_gp_percentage",
        string="GP%",
        help="GP% base on total estimated sale and total cost", store=True
    )
    pick_type = fields.Selection(
        selection=[
            ("picked_by_customer", "Picked By Customer"),
            ("door_delivery", "Door Delivery"),
        ],
        default="door_delivery",
        string="Shipping Method",
    )
    division_type_id = fields.Many2one('division.type', string='Division Type')
    pw_shipping_cost = fields.Float(
        compute="_compute_pw_shipping_cost",
        inverse="_inverse_pw_shipping_cost",
        string="Shipping Cost",
        help="Shipping cost base on product total weight",
        store=True
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account', 'Analytic Account',
        store=True,
        readonly=False, copy=True, check_company=True,  # Unrequired company
        states={'sale': [('readonly', True)], 'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="The analytic account related to a sales order.")
    pending_qty = fields.Integer(string='Pending Qty', compute='_compute_pending_qty_and_status', store=True)
    so_status = fields.Selection([("closed", "Closed"), ("open", "Open")],
                                 string="SO Status", compute='_compute_pending_qty_and_status', store=True)

    # @api.depends('partner_id', 'date_order')
    # def _compute_analytic_account_id(self):
    #     for order in self:
    #         if not order.analytic_account_id:
    #             default_analytic_account = order.env['account.analytic.default'].sudo().account_get(
    #                 partner_id=order.partner_id.id,
    #                 user_id=order.env.uid,
    #                 date=order.date_order,
    #                 company_id=order.company_id.id,
    #             )
    #             order.analytic_account_id = default_analytic_account.analytic_id

    @api.depends("order_line.product_uom_qty")
    def _compute_total_order_quantity(self):
        """Get total order product quantity."""
        for rec in self:
            rec.total_order_quantity = sum(rec.order_line.mapped('product_uom_qty'))

    @api.depends("order_line.total_weight")
    def _compute_total_weight(self):
        # Get total weight of all product.
        for rec in self:
            # rec.total_weight = sum(line.total_weight for line in rec.order_line)
            rec.total_weight = sum(rec.order_line.mapped('total_weight'))

    @api.depends("total_est_landed_cost", "total_est_dcost")
    def _compute_total_cost(self):
        # Get total cost base on (total est. landed cost and total est. dcost).
        for rec in self:
            rec.total_cost = rec.total_est_landed_cost + rec.total_est_dcost

    @api.depends("total_est_sales", "total_cost")
    def _compute_gp_percentage(self):
        # Get total GP% base on (total est. sales and total cost).
        gp_percentage = 0.0
        for rec in self:
            if rec.total_cost > 0:
                gp_percentage = (
                    (rec.total_est_sales - rec.total_cost) / rec.total_cost * 100.0
                )
            rec.gp_percentage = gp_percentage

    @api.depends("order_line")
    def _compute_total_est_sales(self):
        # Get total estimated sales base on untaxed amount.
        for rec in self:
            rec.total_est_sales = rec.amount_untaxed
        # total_est_sales = 0.0
        # for rec in self.order_line:
        #     if rec.list_price and rec.so_quantity:
        #         total_est_sales += rec.list_price * rec.so_quantity
        # self.total_est_sales = total_est_sales
        # for rec in self:
        #     rec.total_est_sales = rec.amount_untaxed

    @api.depends("order_line")
    def _company_total_est_landed_cost(self):
        # Get total estimated landed cost base on SO line sum(LCO).
        for rec in self:
            # rec.total_est_landed_cost = sum(line.landed_cost for line in rec.order_line)
            rec.total_est_landed_cost = sum(rec.order_line.mapped('landed_cost'))

    @api.depends("order_line")
    def _compute_total_est_dcost(self):
        # Get total estimated Dcost cost base on SO line sum(TCO - LCO).
        for rec in self:
            rec.total_est_dcost = (
                sum(line.subtotal_cost for line in rec.order_line)
                - rec.total_est_landed_cost
            )
            rec.total_est_dcost = sum(rec.order_line.mapped('subtotal_cost')) - rec.total_est_landed_cost




    # expected_date = fields.Datetime(
    #     string="Expected Date",
    #     compute='_compute_expected_date', store=True,  # Note: can not be stored since depends on today()
    #     help="Delivery date you can promise to the customer, computed from the minimum lead time of the order lines.")
    """
    @api.depends('order_line.so_quantity', 'order_line.cancelled_qty', 'order_line.product_uom_qty',
                 'order_line.qty_delivered', 'picking_ids.state')
    def _compute_pending_qty_and_status(self):
        cancel_total = 0
        for order in self:
            so_quantity = sum(order.order_line.mapped('so_quantity'))
            cancelled_qty = sum(order.order_line.mapped('cancelled_qty'))

            for order_line in order.order_line:
                cancel_move = order.picking_ids.mapped('move_ids').filtered(lambda x: x.state == 'cancel' and x.product_id.id == order_line.product_id.id and x.picking_type_id.code == 'outgoing' and x.location_id.usage == 'internal')
                cancel_total += sum(cancel_move.mapped('product_uom_qty'))
            all_cancel_total = cancel_total + cancelled_qty

            # product_uom_qty = sum(order.order_line.mapped('product_uom_qty'))
            qty_delivered = sum(order.order_line.mapped('qty_delivered'))
            # pending_qty = (so_quantity - cancelled_qty) - qty_delivered
            pending_qty = (so_quantity - all_cancel_total) - qty_delivered
            order.pending_qty = pending_qty
            if order.state == 'sale':
                if order.pending_qty == 0:
                    order.so_status = 'closed'
                else:
                    order.so_status = 'open'
            else:
                order.so_status = 'open'
    """


    def _inverse_pw_shipping_cost(self):
        pass

    @api.depends('order_line.so_quantity', 'order_line.cancelled_qty', 'order_line.product_uom_qty',
                 'order_line.qty_delivered', 'picking_ids.state')
    def _compute_pending_qty_and_status(self):
        for order in self:
            # Prefetch related records to avoid multiple queries
            order.order_line.mapped('product_id')
            order.picking_ids.mapped('move_ids')

            # Get all quantities in one go
            so_quantity = sum(order.order_line.mapped('so_quantity'))
            cancelled_qty = sum(order.order_line.mapped('cancelled_qty'))
            qty_delivered = sum(order.order_line.mapped('qty_delivered'))

            # Get cancelled moves in one query
            cancel_moves = order.picking_ids.mapped('move_ids').filtered(
                lambda x: x.state == 'cancel' and
                          x.picking_type_id.code == 'outgoing' and
                          x.location_id.usage == 'internal'
            )

            # Calculate cancelled quantity from moves
            cancel_total = sum(cancel_moves.mapped('product_uom_qty'))
            all_cancel_total = cancel_total + cancelled_qty

            # Calculate pending quantity
            pending_qty = (so_quantity - all_cancel_total) - qty_delivered
            order.pending_qty = pending_qty

            # Set status based on state and pending quantity
            order.so_status = 'closed' if order.state == 'sale' and pending_qty == 0 else 'open'

    @api.depends("pick_type", "total_weight", "carrier_id")
    def _compute_pw_shipping_cost(self):
        # Get shipping cost base on delivery method and total weight).
        pw_shipping_cost = 0.0
        for rec in self:
            if (
                rec.total_weight > 0
                and rec.pick_type == "door_delivery"
            ):
                if rec.carrier_id.delivery_type == "fixed":
                    pw_shipping_cost = (
                        rec.carrier_id.fixed_price / rec.total_weight
                    ) * rec.total_weight
                elif rec.carrier_id.delivery_type == "base_on_rule":
                    vals = rec.carrier_id.rate_shipment(rec)
                    pw_shipping_cost = (
                        vals["carrier_price"] / rec.total_weight
                    ) * rec.total_weight
            rec.pw_shipping_cost = pw_shipping_cost

    def action_confirm(self):
        # Restore original sequence if set
        for order in self:
            if order.presale_original_name:
                order.name = order.presale_original_name
        res = super().action_confirm()
        # Add panworld custom fields values.
        for rec in self:
            rec.picking_ids.write({
                "customer_sales_order": rec.customer_sales_order,
                "analytic_account_id": rec.analytic_account_id.id or False,
                "division_type_id": rec.division_type_id.id or False
            })
            if rec.is_imported:
                rec.date_order = rec.customer_so_date

            tax_sets = []
            for line in rec.order_line:
                tax_ids = tuple(sorted(line.tax_ids))
                if tax_ids not in tax_sets:
                    tax_sets.append(tax_ids)

            if len(tax_sets) > 1:
                raise ValidationError("Please check the taxes and make them unique.")
            # if (
            #     not rec.order_line.filtered(lambda l: l.product_id.landed_cost_ok)
            #     and rec.pick_type != "picked_by_customer"
            # ):
            #     raise ValidationError(
            #         _("Please add shipping cost to confirm this order!")
            #     )
        return res

    # @api.onchange("partner_id")
    # def onchange_partner_id(self):
    #     res = super().onchange_partner_id()
    #     if self.partner_id and self.partner_id.pick_type:
    #         self.pick_type = self.partner_id.pick_type
    #         if self.partner_id.pick_type == "door_delivery":
    #             self.carrier_id = (
    #                 self.partner_id.property_delivery_carrier_id.id or False
    #             )
    #     # self.analytic_account_id = self.partner_id.analytic_account_id or False
    #     self.division_type_id = self.partner_id.division_type_id or False
    #     return res

    def action_set_quotation_date(self):
        """ Method to pass CSO date in SO date"""
        for order in self:
            if order.is_imported:
                order.date_order = order.customer_so_date

    def action_view_wiz_update_order_date(self):
        wiz_view_id = self.env.ref("panworld_sale.view_wiz_update_order_form")
        return {
            "name": "Update Order Date",
            "view_type": "form",
            "view_mode": "form",
            "view_id": wiz_view_id.id,
            "res_model": "wiz.update.order.date",
            "type": "ir.actions.act_window",
            "target": "new",
        }

    def action_export_xls(self, mail_attach=False):
        self.ensure_one()
        return self.env['sale.xls.wizard'].action_export_xls(self.id, mail_attach)

    @api.model
    def _prepare_purchase_order_line_data(self, so_line, date_order, company):
        """ Generate purchase order line values, from the SO line
            :param so_line : origin SO line
            :rtype so_line : sale.order.line record
            :param date_order : the date of the orgin SO
            :param company : the company in which the PO line will be created
            :rtype company : res.company record
        """
        # price on PO so_line should be so_line - discount
        res = super()._prepare_purchase_order_line_data(so_line, date_order, company)
        price = so_line.price_unit - (so_line.price_unit * (so_line.discount / 100))
        price = so_line.product_id and so_line.product_uom_id._compute_price(price, so_line.product_id.uom_id) or price
        quantity = so_line.product_id and so_line.product_uom_id._compute_quantity(so_line.product_uom_qty,
                                                                                so_line.product_id.uom_id) or so_line.product_uom_qty
        po_qty = so_line.product_id and so_line.product_uom_id._compute_quantity(so_line.so_quantity,
                                                                              so_line.product_id.uom_id) or so_line.so_quantity
        rfq_qty = so_line.product_id and so_line.product_uom_id._compute_quantity(so_line.so_qty,
                                                                               so_line.product_id.uom_id) or so_line.so_qty

        res.update({'list_price': price or 0.0,
                    'po_list_price': price or 0.0,
                    'po_qty': po_qty,
                    'rfq_qty': rfq_qty,
                    'to_be_received_qty': quantity,
                    'related_so': self.id
                    })
        return res



    @api.onchange('commitment_date', 'expected_date')
    def _onchange_commitment_date(self):
        # Override the original method to show nothing as warning
        pass


    def create_sale_return(self):
        """Create return of purchase and redirect to RMA."""
        all_pickings_done = all(picking.state == 'done' for picking in self.picking_ids)
        if not all_pickings_done:
            raise ValidationError(_('Please confirm the deliveries first.'))
        else:
            ctx = self.env.context.copy()
            ctx.update({
                    "from_sale_return": True,
                    "default_rma_type": "customer",
                    "default_partner_id": self.partner_id.id,
                    "default_sale_order_id": self.id,
                })
            return {
                "type": "ir.actions.act_window",
                "res_model": "rma.ret.mer.auth",
                "view_mode": "form",
                "context": ctx,
                "name": "Return",
            }

    @api.model_create_multi
    def create(self, vals_list):
        orders = super(SaleOrder, self).create(vals_list)
        for order in orders:
            if order.state in ['draft', 'sent', 'cancel']:
                order.presale_original_name = order.name
                # Swap Prefix: SO -> Q
                if order.name.startswith('SO'):
                    order.name = order.name.replace('SO', 'Q', 1)
        return orders

