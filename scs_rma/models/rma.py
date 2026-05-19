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
from odoo.exceptions import ValidationError, UserError


class RMARetMerAuth(models.Model):
    _name = "rma.ret.mer.auth"
    _inherit = ['mail.thread']
    _description = "Return Merchandise Authorization"

    def _get_company(self):
        return self.env.company

    name = fields.Char("RMA No", readonly=True)
    rma_type = fields.Selection(
        [
            ("customer", "Sale Order"),
            ("supplier", "Purchase Order"),
            ("picking", "Picking"),
            ("lot", "Serial No"),
            ("direct", "Purchase Direct"),
            ("invoice", "Invoice"),
            ("sale_direct", "Sale Direct"),
        ],
        string="RMA Type",
        default="customer",
    )

    problem = fields.Text("Notes")
    rma_date = fields.Date("Date", default=fields.Date.context_today, help="Date")
    partner_id = fields.Many2one("res.partner", "Customer")
    supplier_id = fields.Many2one("res.partner", "Supplier")
    picking_partner_id = fields.Many2one("res.partner", "Partner")
    sale_order_id = fields.Many2one("sale.order", string="Sale Order", copy=False)
    purchase_order_id = fields.Many2one("purchase.order", "Purchase Order", copy=False)
    picking_rma_id = fields.Many2one("stock.picking", "Picking", copy=False)
    rma_lot = fields.Char("Serial No", copy=False)
    rma_sale_lines_ids = fields.One2many(
        "rma.sale.lines",
        "rma_id",
        string="Order Lines",
        states={
            "resolved": [("readonly", True)],
            "close": [("readonly", True)],
            "approve": [("readonly", True)],
        },
        copy=False,
    )
    rma_purchase_lines_ids = fields.One2many(
        "rma.purchase.lines",
        "rma_id",
        string="Purchase Order Lines",
        states={
            "resolved": [("readonly", True)],
            "close": [("readonly", True)],
            "approve": [("readonly", True)],
        },
        copy=False,
    )
    rma_picking_lines_ids = fields.One2many(
    "rma.picking.lines",
        "rma_id",
        string="Picking Lines",
        states={
            "resolved": [("readonly", True)],
            "close": [("readonly", True)],
            "approve": [("readonly", True)],
        },
        copy=False,
    )
    stock_picking_ids = fields.One2many(
        "stock.picking", "rma_id", string="Stock Pickings", copy=False
    )
    invoice_ids = fields.One2many(
        "account.move", "rma_id", string="Invoices", copy=False
    )
    pick_count = fields.Integer(string="Pickings Count", compute="_count_picking_ids", store=True)
    inv_count = fields.Integer(string="Invoice Count", compute="_count_invoice_ids", store=True)
    state = fields.Selection(
        [
            ("new", "New"),
            ("verification", "Verification"),
            ("resolved", "Waiting For Delivery"),
            ("approve", "Approved"),
            ("close", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="Status", tracking=True,
        default="new",
    )
    type = fields.Selection(
        [("return", "Return"), ("exchange", "Exchange")], string="Actions"
    )
    amount_untaxed = fields.Float(
        string="Untaxed Amount", store=True, readonly=True, compute="_amount_all"
    )
    amount_tax = fields.Float(
        string="Taxes", store=True, readonly=True, compute="_amount_all"
    )
    amount_total = fields.Float(
        string="Total", store=True, readonly=True, compute="_amount_all"
    )
    purchase_amount_untaxed = fields.Float(
        string="Untaxed Amount",
        store=True,
        readonly=True,
        compute="_purchase_amount_all",
    )
    purchase_amount_tax = fields.Float(
        string="Taxes", store=True, readonly=True, compute="_purchase_amount_all"
    )
    purchase_amount_total = fields.Float(
        string="Total", store=True, readonly=True, compute="_purchase_amount_all"
    )
    picking_amount_untaxed = fields.Float(
        string="Untaxed Amount", store=True, compute="_picking_amount_all"
    )
    picking_amount_tax = fields.Float(
        string="Taxes", store=True, compute="_picking_amount_all"
    )
    picking_amount_total = fields.Float(
        string="Total", store=True, compute="_picking_amount_all"
    )
    pick_origin = fields.Char(
        string="Previous RMA", related="picking_rma_id.origin", readonly=True
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=False,
    )
    company_id = fields.Many2one("res.company", string="Company", default=_get_company)
    invoice_status = fields.Selection(
        [("pending", "Pending"), ("paid", "Paid")],
        string="Invoice Status",
        default="pending",
        compute="_get_invoice_status",
    )
    lot_picking_id = fields.Many2one("stock.picking", "Lot Picking", copy=False)
    picking_customer_id = fields.Many2one("res.partner", "Customer")
    picking_supplier_id = fields.Many2one("res.partner", "Supplier")
    is_imported = fields.Boolean(
        string="Is imported?", help="Import sale return from sheet", copy=False
    )

    rma_direct_lines_ids = fields.One2many(
        "rma.direct.lines",
        "rma_id",
        string="Direct Order Lines",
        states={
            "resolved": [("readonly", True)],
            "close": [("readonly", True)],
            "approve": [("readonly", True)],
        },
        copy=False,
    )
    rma_sale_direct_lines_ids = fields.One2many(
        "rma.sale.direct.lines",
        "rma_id",
        string="Direct Order Lines",
        states={
            "resolved": [("readonly", True)],
            "close": [("readonly", True)],
            "approve": [("readonly", True)],
        },
        copy=False,
    )
    rma_inv_lines_ids = fields.One2many(
        "rma.invoice.lines",
        "rma_id",
        string="Invoice Order Lines",
        states={
            "resolved": [("readonly", True)],
            "close": [("readonly", True)],
            "approve": [("readonly", True)],
        },
        copy=False,
    )
    move_id = fields.Many2one("account.move", string="Bill", copy=False)

    @api.onchange("move_id")
    def _onchange_move_id(self):
        """
            Onchange of Bill it will auto-populate lines from
            Bill lines
        """
        inv_line_lst = []
        for order_line in self.move_id.invoice_line_ids:
            rma_inv_line = (
                0,
                0,
                {
                    "product_id": order_line.product_id
                                  and order_line.product_id.id
                                  or False,
                    "total_qty": order_line.quantity or 0,
                    "refund_qty": order_line.quantity or 0,
                    "refund_price": order_line.price_unit * order_line.quantity,
                    "order_quantity": order_line.quantity or 0,
                    "delivered_quantity": order_line.quantity,
                    "total_price": order_line.price_total,
                    "price_unit": order_line.price_unit or 0,
                    "source_location_id": self.move_id.company_id.sup_source_location_id.id
                                          or False,
                    "destination_location_id": self.move_id.company_id.sup_destination_location_id.id
                                               or False,
                    "type": "return",
                    "tax_id": order_line.tax_ids,
                },
            )
            inv_line_lst.append(rma_inv_line)
        self.rma_inv_lines_ids = [(5,)]
        self.rma_inv_lines_ids = inv_line_lst

    @api.depends(
        "rma_purchase_lines_ids.refund_price",
        "rma_direct_lines_ids.refund_price",
        "rma_sale_direct_lines_ids.refund_price",
        "rma_inv_lines_ids.refund_price",
        "rma_sale_lines_ids.refund_price",
    )
    def _amount_all(self):
        """Compute the total amounts based on RMA type."""
        for order in self:
            amount_untaxed = amount_tax = 0.0
            if order.rma_type == "sale_direct":
                for line in order.rma_sale_direct_lines_ids:
                    amount_untaxed += line.refund_price
                    amount_tax += line.price_tax
            elif order.rma_type == "direct":
                for line in order.rma_direct_lines_ids:
                    amount_untaxed += line.refund_price
                    amount_tax += line.price_tax
            elif order.rma_type == "invoice":
                for line in order.rma_inv_lines_ids:
                    amount_untaxed += line.refund_price
                    amount_tax += line.price_tax
            elif order.rma_type == "supplier":
                 for line in order.rma_purchase_lines_ids:
                    amount_untaxed += line.refund_price
                    amount_tax += line.price_tax
            else:
                for line in order.rma_sale_lines_ids:
                    amount_untaxed += line.refund_price
                    amount_tax += line.price_tax

            order.update(
                {
                    "amount_untaxed": amount_untaxed,
                    "amount_tax": amount_tax,
                    "amount_total": amount_untaxed + amount_tax,
                    "purchase_amount_untaxed": amount_untaxed if order.rma_type in ["direct", "invoice", "supplier"] else 0.0,
                    "purchase_amount_tax": amount_tax if order.rma_type in ["direct", "invoice", "supplier"] else 0.0,
                    "purchase_amount_total": (amount_untaxed + amount_tax) if order.rma_type in ["direct", "invoice", "supplier"] else 0.0,
                }
            )



    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        for rma in self:
            if not self.env.context.get("from_sale_return"):
                rma.sale_order_id = False

    @api.onchange("supplier_id")
    def _onchange_supplier_id(self):
        for rma in self:
            if not self.env.context.get("from_purchase_return"):
                rma.purchase_order_id = False

    @api.onchange("picking_partner_id")
    def _onchange_picking_partner_id(self):
        for rma in self:
            rma.picking_rma_id = False

    @api.onchange("rma_lot")
    def _onchange_rma_lot(self):
        for rma in self:
            rma.lot_picking_id = False

    @api.onchange("partner_id", "supplier_id", "picking_rma_id", "lot_picking_id")
    def _onchange_partners(self):
        for rma in self:
            if rma.partner_id:
                rma.picking_customer_id = rma.partner_id.id
                rma.picking_supplier_id = False
            elif rma.supplier_id:
                rma.picking_customer_id = False
                rma.picking_supplier_id = rma.supplier_id.id
            elif rma.picking_rma_id:
                if rma.picking_rma_id.sale_id:
                    rma.picking_customer_id = rma.picking_rma_id.partner_id.id
                    rma.picking_supplier_id = False
                if rma.picking_rma_id.purchase_id:
                    rma.picking_customer_id = False
                    rma.picking_supplier_id = rma.picking_rma_id.partner_id.id
            else:
                rma.picking_customer_id = False
                rma.picking_supplier_id = False

    @api.onchange("rma_type")
    def _onchange_rma_type(self):
        for rma in self:
            if not self.env.context.get("from_purchase_return") and not self.env.context.get("from_sale_return"):
                rma.sale_order_id = (
                    rma.purchase_order_id
                ) = (
                    rma.picking_rma_id
                ) = (
                    rma.lot_picking_id
                ) = (
                    rma.partner_id
                ) = rma.supplier_id = rma.picking_partner_id = rma.rma_lot = False
            rma.rma_sale_lines_ids = (
                rma.rma_picking_lines_ids
            ) = (
                rma.rma_purchase_lines_ids
            ) = (
                rma.rma_inv_lines_ids
            ) = rma.rma_direct_lines_ids = rma.rma_sale_direct_lines_ids = False

    @api.onchange("rma_type", "sale_order_id", "purchase_order_id", "company_id")
    def _onchange_sale_purchase_type(self):
        for rma in self:
            if rma.rma_type in ('customer', 'supplier'):
                self.currency_id = self.company_id.currency_id
                if self.sale_order_id.currency_id:
                    self.currency_id = self.sale_order_id.currency_id
                if self.purchase_order_id.currency_id:
                    self.currency_id = self.purchase_order_id.currency_id
            else:
                self.currency_id = self.company_id.currency_id

    @api.constrains("sale_order_id")
    def _check_sale_order_id_duplicate(self):
        for rec in self.filtered(lambda r: r.sale_order_id):
            duplicate_rma = rec.search(
                [
                    ("sale_order_id", "=", rec.sale_order_id.id),
                    ("id", "!=", rec.id),
                    ("state", "!=", "cancelled"),
                ]
            )
            # Remove the Validation as per requirement on 08-08-2025
            # if duplicate_rma:
            #     raise ValidationError(
            #         "Duplicate order %s already exist for the same sale order."
            #         % duplicate_rma[0].name
            #     )

    @api.constrains("purchase_order_id")
    def _check_purchase_order_id_duplicate(self):
        for rec in self.filtered(lambda r: r.purchase_order_id):
            duplicate_rma = rec.search(
                [
                    ("purchase_order_id", "=", rec.purchase_order_id.id),
                    ("id", "!=", rec.id),
                    ("state", "!=", "cancelled"),
                ]
            )
            if duplicate_rma:
                raise ValidationError(
                    "Duplicate order %s already exist for the same purchase order."
                    % duplicate_rma[0].name
                )

    @api.constrains("picking_rma_id")
    def _check_picking_rma_id_duplicate(self):
        for rec in self.filtered(lambda r: r.picking_rma_id):
            duplicate_rma = rec.search(
                [
                    ("picking_rma_id", "=", rec.picking_rma_id.id),
                    ("id", "!=", rec.id),
                    ("state", "!=", "cancelled"),
                ]
            )
            if duplicate_rma:
                raise ValidationError(
                    "Duplicate order %s already exist for the same picking order."
                    % duplicate_rma[0].name
                )

    @api.constrains("rma_lot", "lot_picking_id")
    def _check_lot_rma_duplicate(self):
        for rec in self.filtered(lambda r: r.rma_lot and r.lot_picking_id):
            duplicate_rma = rec.search(
                [
                    ("rma_lot", "=", rec.rma_lot),
                    ("lot_picking_id", "=", rec.lot_picking_id.id),
                    ("id", "!=", rec.id),
                    ("state", "!=", "cancelled"),
                ]
            )
            if duplicate_rma:
                raise ValidationError(
                    "Duplicate order %s already exist for the same lot number."
                    % duplicate_rma[0].name
                )

    @api.depends("rma_picking_lines_ids")
    def _picking_amount_all(self):
        """Compute the total amounts of the PO."""
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.rma_picking_lines_ids:
                amount_untaxed += line.refund_price
                amount_tax += line.price_tax
            order.update(
                {
                    "picking_amount_untaxed": amount_untaxed,
                    "picking_amount_tax": amount_tax,
                    "picking_amount_total": amount_untaxed + amount_tax,
                }
            )

    @api.depends("stock_picking_ids")
    def _count_picking_ids(self):
        """ Compute total count of pickings """
        for rma in self:
            rma.pick_count = (
                rma.stock_picking_ids and len(rma.stock_picking_ids.ids) or 0
            )

    @api.depends("invoice_ids")
    def _count_invoice_ids(self):
        """ Compute total count of invoices """
        for rma in self:
            rma.inv_count = rma.invoice_ids and len(rma.invoice_ids.ids) or 0

    def rma_lines_set_qty_zero(self):
        for line in self.rma_sale_lines_ids:
            line.refund_qty = 0

    def rma_cancel(self):
        for rma in self:
            if any(pick.state == "done" for pick in rma.stock_picking_ids):
                raise ValidationError(
                    _("Cannot cancel RMA as few pickings are already done.")
                )
            if any(inv.state == "posted" for inv in rma.invoice_ids):
                raise ValidationError(
                    _("Cannot cancel RMA as one or more invoices are already posted.")
                )
            rma.stock_picking_ids.filtered(
                lambda p: p.state != "cancel"
            ).sudo().action_cancel()
            rma.invoice_ids.filtered(lambda inv: inv.state == "draft").button_cancel()
            rma.state = "cancelled"

    def _get_invoice_status(self):
        for rma in self:
            rma.invoice_status = "pending"
            inv_states = rma.invoice_ids.mapped("payment_state")
            if inv_states and all(state == "paid" for state in inv_states):
                rma.invoice_status = "paid"

    def rma_submit(self):
        """Set state to verification."""
        if self.rma_type == "lot" and not self.lot_picking_id:
            raise ValidationError(_("You can not submit blank RMA."))
        self.write({"state": "verification"})
        return True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('rma.rma') or _('New')
        return super().create(vals_list)

    # @api.model_create_multi
    # def create(self, vals_list):
    #     """ Create Sequence for RMA """
    #     records = super(RMARetMerAuth, self).create(vals_list)
    #     for vals in vals_list:
    #         sequence_val = self.env["ir.sequence"].next_by_code("rma.rma") or "/"
    #         vals.update({"name": sequence_val})
    #     return records

    def rma_close(self):
        """ Set state to Close. if all Pickings are done """
        for rec in self:
            if rec.rma_type == "invoice" and rec.move_id:
                rec.move_id.rma_done = True
            # Don't allow to close RMA, if any picking is cancelled.
            cancelled_pickings = rec.stock_picking_ids.filtered(
                lambda p: p.state == "cancel"
            )
            if cancelled_pickings:
                raise ValidationError(
                    _("Cannot close RMA as few pickings are cancelled.")
                )

            picking = rec.stock_picking_ids.filtered(
                lambda pick: pick.state not in ["done", "cancel"]
            )
            if picking:
                raise ValidationError(_("Please validate all the pickings first."))
            rec.write({"state": "close"})
            if rec.rma_type == "customer":
                rma_ids = self.env["rma.ret.mer.auth"].search(
                    [("sale_order_id", "=", rec.sale_order_id.id),]
                )
                # Check if Sale Order is Fully Returned or Not
                # Prepare all RMA product with return qty
                rma_product_list = {}
                for rma in rma_ids:
                    for line in rma.rma_sale_lines_ids:
                        if rma_product_list.get(line.product_id.id):
                            rma_product_list[line.product_id.id] += line.refund_qty
                        else:
                            rma_product_list[line.product_id.id] = line.refund_qty
                # Prepare all SO product with Delivered qty
                so_product_list = {}
                for so_line in rma.sale_order_id.order_line:
                    if so_product_list.get(so_line.product_id.id):
                        so_product_list[so_line.product_id.id] += so_line.qty_delivered
                    else:
                        so_product_list[so_line.product_id.id] = so_line.qty_delivered
                # Check if RMA's product return qty is equal to sale order delivered
                flag = False
                for product, qty in rma_product_list.items():
                    if so_product_list.get(product) != qty:
                        flag = True
                        break
                if not flag:
                    rec.sale_order_id.rma_done = True
            if rec.rma_type == "supplier" and rec.purchase_order_id:
                rec.purchase_order_id.rma_done = True
            if rec.rma_type == "picking" and rec.picking_rma_id:
                rec.picking_rma_id.rma_done = True
            rec.write({"state": "close"})

    def rma_approve(self):
        """Set state to approve."""
        for rec in self:
            rec.write({"state": "approve"})

    def rma_set_draft(self):
        """Set state to New."""
        for rec in self:
            for pick in rec.stock_picking_ids.filtered(lambda p: p.state == "done"):
                raise ValidationError(
                    _("You can not set to draft as picking is already done.")
                )
            for inv in rec.invoice_ids.filtered(lambda r: r.state == "posted"):
                raise ValidationError(
                    _("You can not set to draft as Invoice is already posted.")
                )
            rec.write({"state": "new"})

    def check_serial(self):
        """Fetch data from serial no."""
        for rec in self:
            lot_no = self.env["stock.lot"].search(
                [("name", "=", rec.rma_lot)]
            )
            if len(lot_no) > 1:
                raise ValidationError(
                    _(
                        "Two products found for this Serial Number. It should be unique per product."
                    )
                )
            if not lot_no:
                raise ValidationError(_("Serial No. not found"))
            move_line = self.env["stock.move.line"].search(
                [("lot_id", "=", lot_no[0].id), ("state", "=", "done")], order="id desc"
            )
            move_line = move_line and move_line[0] or False
            pick_id = move_line and move_line.move_id.picking_id or False
            if not pick_id:
                raise ValidationError(_("No picking found for this Serial No."))
            rec.lot_picking_id = pick_id.id
            if rec.lot_picking_id:
                if rec.lot_picking_id.sale_id:
                    rec.picking_customer_id = rec.lot_picking_id.partner_id.id
                    rec.picking_supplier_id = False
                if rec.lot_picking_id.purchase_id:
                    rec.picking_customer_id = False
                    rec.picking_supplier_id = rec.lot_picking_id.partner_id.id
            rec._onchange_lot_picking_id()

    def prepare_stock_move_vals(self, rma_line, rma):
        move_vals = {
            "product_id": rma_line.product_id.id or False,
            "description_picking": rma_line.product_id.name or False,
            # "name": rma_line.product_id.name or False,
            "origin": rma.name,
            "product_uom_qty": rma_line.refund_qty or 0,
            "product_uom": rma_line.product_id.uom_id.id or False,
            "rma_id": rma.id,
            "price_unit": rma_line.price_subtotal or 0,
        }
        if rma.rma_type == "customer":
            move_vals.update(
                {
                    "location_id": rma_line.source_location_id.id or False,
                    "location_dest_id": rma_line.destination_location_id.id or False,
                    # "group_id": rma.sale_order_id.procurement_group_id.id,
                }
            )
        if rma.rma_type == "supplier":
            move_vals.update(
                {
                    "location_id": rma_line.source_location_id.id or False,
                    "location_dest_id": rma_line.destination_location_id.id or False,
                    # "group_id": rma.purchase_order_id.group_id.id,
                }
            )
        if rma.rma_type in ["picking", "lot"]:
            move_vals.update(
                {
                    "location_id": rma_line.destination_location_id.id or False,
                    "location_dest_id": rma_line.source_location_id.id or False,
                }
            )
        if rma.rma_type in ["direct", "invoice", "sale_direct"]:
            move_vals.update(
                {
                    "location_id": rma_line.source_location_id.id or False,
                    "location_dest_id": rma_line.destination_location_id.id or False,
                }
            )
            if rma.purchase_order_id:
                move_vals.update({"group_id": rma.purchase_order_id.group_id.id})
        return move_vals

    def prepare_exchange_stock_move_vals(self, rma_line, rma):
        ex_move_vals = {
            "product_id": rma_line.exchange_product_id.id or False,
            # "name": rma_line.exchange_product_id.name or False,
            "origin": rma.name,
            "product_uom_qty": rma_line.refund_qty or 0,
            "product_uom": rma_line.exchange_product_id.uom_id.id or False,
            "rma_id": rma.id,
            "price_unit": rma_line.price_subtotal or 0,
        }
        if rma.rma_type == "customer":
            ex_move_vals.update(
                {
                    "location_id": rma_line.destination_location_id.id or False,
                    "location_dest_id": rma_line.source_location_id.id or False,
                    "group_id": rma.sale_order_id.procurement_group_id.id,
                }
            )
        if rma.rma_type == "supplier":
            ex_move_vals.update(
                {
                    "location_id": rma_line.destination_location_id.id or False,
                    "location_dest_id": rma_line.source_location_id.id or False,
                    "group_id": rma.purchase_order_id.group_id.id,
                }
            )
        if rma.rma_type in ["picking", "lot"]:
            ex_move_vals.update(
                {
                    "location_id": rma_line.source_location_id.id or False,
                    "location_dest_id": rma_line.destination_location_id.id or False,
                }
            )
        return ex_move_vals

    def prepare_inv_line_vals(self, rma_line, prod_price, rma):
        inv_line_values = {
            "product_id": rma_line.product_id.id or False,
            "name": rma_line.product_id.name or False,
            "quantity": rma_line.refund_qty or 0,
            "price_unit": prod_price or 0,
            "currency_id": rma.currency_id.id or False,
        }
        return inv_line_values

    def prepare_exchange_inv_line_vals(self, rma_line, inv_account_id, rma):
        inv_line_vals_exchange = {
            "product_id": rma_line.exchange_product_id.id or False,
            "account_id": inv_account_id or False,
            "name": rma_line.exchange_product_id.name or False,
            "quantity": rma_line.refund_qty or 0,
            "currency_id": rma.currency_id.id or False,
        }
        return inv_line_vals_exchange

    def prepare_picking_vals(self, picking_type_id, rma, move):
        picking_vals = {
            "move_type": "one",
            "picking_type_id": picking_type_id or False,
            "origin": rma.name,
            "move_ids": [(0, 0, move[2])],
            "location_id": move[2]["location_id"],
            "location_dest_id": move[2]["location_dest_id"],
            "rma_id": rma.id,
        }
        return picking_vals

    def prepare_invoice_vals(self, rma, invoice_line_vals):
        inv_values = {
            "invoice_origin": rma.name or "",
            "narration": rma.problem or "",
            "invoice_line_ids": invoice_line_vals,
            "invoice_date": rma.rma_date or False,
            "rma_id": rma.id,
            "currency_id": rma.currency_id.id or False,
        }
        if rma.rma_type == 'customer':
            inv_values.update({
                "tracking_ref": rma.sale_order_id.customer_sales_order or '',
                "payment_reference": rma.sale_order_id.name,
                "analytic_account_id": rma.partner_id.analytic_account_id.id or False,
                "division_type_id": rma.partner_id.division_type_id.id or False
            })
            if rma.partner_id.journal_id:
                inv_values.update({
                    "journal_id": rma.partner_id.journal_id.id,
                })
        elif rma.rma_type == 'supplier':
            inv_values.update({
                "po_ref_ids": [(4, rma.purchase_order_id.id)]
            })
        return inv_values

    def create_receive_picking(self):
        """
        Create Receive picking for RMA Customer and set RMA state to.
        resolved. Create refund invoices for return type RMA.
        """
        stock_move_obj = self.env["stock.move"]
        stock_picking_obj = self.env["stock.picking"]
        stock_pick_type_obj = self.env["stock.picking.type"]
        account_move_obj = self.env["account.move"]
        domain = [
            (
                "warehouse_id.company_id",
                "in",
                [
                    self.env.context.get("company_id", self.env.user.company_id.id),
                    False,
                ],
            )
        ]
        in_domain = [("code", "=", "incoming")] + domain
        out_domain = [("code", "=", "outgoing")] + domain
        for rma in self:
            # When Type is customer then it will create Incoming Picking
            if rma.rma_type == "sale_direct":
                moves_vals = []
                invoice_vals = []
                in_domain = [
                    ("warehouse_id.company_id", "in", [rma.company_id.id, False, ],),
                    ("code", "=", "incoming")
                ]
                out_domain = [
                    ("warehouse_id.company_id", "in", [rma.company_id.id, False, ],),
                    ("code", "=", "outgoing")
                ]
                state = "draft"
                for line in rma.rma_sale_direct_lines_ids:
                    state = "approve"
                    # Prepare Move Vals for Delivery Picking
                    rma_move_vals = rma.prepare_stock_move_vals(line, rma)
                    rma_move_vals.update(
                        {"purchase_line_id": False, }
                    )
                    moves_vals.append((0, 0, rma_move_vals))
                    inv_ex_account_id = (
                            line.product_id.property_account_expense_id
                            and line.product_id.property_account_expense_id.id
                            or line.product_id.categ_id.property_account_expense_categ_id
                            and line.product_id.categ_id.property_account_expense_categ_id.id
                            or False
                    )
                    if not inv_ex_account_id:
                        raise ValidationError(
                            ('No account defined for product "%s".')
                            % line.product_id.name
                        )
                    prod_price = 0.0
                    if line.refund_qty != 0:
                        prod_price = float((line.refund_price) / float(line.refund_qty))
                    # PO : Invoice Line vals for Vendor Refund
                    inv_line_vals = rma.prepare_inv_line_vals(line, prod_price, rma)
                    inv_line_vals.update({'rma_sale_direct_line_id': line.id or False})
                    if line.tax_id and line.tax_id.ids:
                        inv_line_vals.update({"tax_ids": [(6, 0, line.tax_id.ids)]})
                    invoice_vals.append((0, 0, inv_line_vals))
                new_picking = False
                for move in moves_vals:
                    picking = stock_picking_obj.search(
                        [
                            ("rma_id", "=", rma.id),
                            ("location_id", "=", move[2].get("location_id")),
                            ("location_dest_id", "=", move[2].get("location_dest_id")),
                        ]
                    )
                    # If no picking found, then create one
                    if not picking:
                        picking_type_id = stock_pick_type_obj.search(
                            in_domain, limit=1
                        ).id

                        picking_re_vals = rma.prepare_picking_vals(
                            picking_type_id, rma, move
                        )
                        picking_re_vals.update(
                            {
                                "partner_id": rma.partner_id
                                              and rma.partner_id.id
                                              or False
                            }
                        )
                        picking_rec_re = stock_picking_obj.create(picking_re_vals)
                        new_picking = picking_rec_re
                        picking_rec_re.action_confirm()
                        picking_rec_re.action_assign()
                    else:
                        # If already picking exist, then add move to picking
                        move[2]["picking_id"] = picking.id
                        stock_move_obj.create(move[2])
                        new_picking = picking

                if new_picking:
                    # Get the serial number from RMA's purchase order's move lines and update the same on RMA picking.
                    for move in new_picking.move_ids:
                        demand_qty = move.product_uom_qty
                        order_line = (
                                rma.rma_sale_direct_lines_ids
                                and rma.rma_sale_direct_lines_ids.filtered(
                            lambda l: l.product_id.id == move.product_id.id
                        )
                                or False
                        )
                        lot_ids = (
                                order_line
                                and order_line.rma_id.stock_picking_ids
                                and order_line.rma_id.stock_picking_ids.mapped(
                            "move_ids"
                        ).mapped("lot_ids")
                                or []
                        )
                        if lot_ids:
                            for i in range(0, int(demand_qty)):
                                new_move_line_vals = {
                                    "move_id": move.id,
                                    "product_id": move.product_id.id,
                                    "product_uom": move.product_uom.id,
                                    "qty_done": 1,
                                    "location_id": move.location_id.id,
                                    "location_dest_id": move.location_dest_id.id,
                                    "picking_id": move.picking_id.id,
                                    "lot_id": lot_ids and lot_ids[i].id or False,
                                }
                                sml = (
                                    rma.env["stock.move.line"]
                                    .sudo()
                                    .create(new_move_line_vals)
                                )
                    new_picking.action_confirm()
                    new_picking.action_assign()
                # Create invoice vals for refund
                if invoice_vals:
                    inv_values = rma.prepare_invoice_vals(rma, invoice_vals)
                    inv_values.update(
                        {
                            "move_type": "out_refund",
                            "partner_id": rma.partner_id and rma.partner_id.id or False,
                        }
                    )
                    move = account_move_obj.create(inv_values)
                    move._onchange_partner_id()
                rma.write({"state": state})

            elif rma.rma_type == "direct":
                moves_vals = []
                invoice_vals = []
                in_domain = [
                    ("warehouse_id.company_id", "in", [rma.company_id.id, False, ],),
                    ("code", "=", "incoming")
                ]
                out_domain = [
                    ("warehouse_id.company_id", "in", [rma.company_id.id, False, ],),
                    ("code", "=", "outgoing")
                ]
                state = "draft"
                for line in rma.rma_direct_lines_ids:
                    state = "approve"
                    # Prepare Move Vals for Delivery Picking
                    rma_move_vals = rma.prepare_stock_move_vals(line, rma)
                    rma_move_vals.update(
                        {"purchase_line_id": False, }
                    )
                    moves_vals.append((0, 0, rma_move_vals))
                    inv_ex_account_id = (
                            line.product_id.property_account_expense_id
                            and line.product_id.property_account_expense_id.id
                            or line.product_id.categ_id.property_account_expense_categ_id
                            and line.product_id.categ_id.property_account_expense_categ_id.id
                            or False
                    )
                    if not inv_ex_account_id:
                        raise ValidationError(
                            ('No account defined for product "%s".')
                            % line.product_id.name
                        )
                    prod_price = 0.0
                    if line.refund_qty != 0:
                        prod_price = float((line.refund_price) / float(line.refund_qty))
                    # PO : Invoice Line vals for Vendor Refund
                    inv_line_vals = rma.prepare_inv_line_vals(line, prod_price, rma)
                    if line.tax_id and line.tax_id.ids:
                        inv_line_vals.update({"tax_ids": [(6, 0, line.tax_id.ids)]})
                    invoice_vals.append((0, 0, inv_line_vals))
                new_picking = False
                for move in moves_vals:
                    picking = stock_picking_obj.search(
                        [
                            ("rma_id", "=", rma.id),
                            ("location_id", "=", move[2].get("location_id")),
                            ("location_dest_id", "=", move[2].get("location_dest_id")),
                        ]
                    )
                    # If no picking found, then create one
                    if not picking:
                        picking_type_id = stock_pick_type_obj.search(
                            out_domain, limit=1
                        ).id
                        picking_re_vals = rma.prepare_picking_vals(
                            picking_type_id, rma, move
                        )
                        picking_re_vals.update(
                            {
                                "partner_id": rma.supplier_id
                                              and rma.supplier_id.id
                                              or False
                            }
                        )
                        picking_rec_re = stock_picking_obj.create(picking_re_vals)
                        new_picking = picking_rec_re
                        picking_rec_re.action_confirm()
                        picking_rec_re.action_assign()
                    else:
                        # If already picking exist, then add move to picking
                        move[2]["picking_id"] = picking.id
                        stock_move_obj.create(move[2])
                        new_picking = picking

                # Get the serial number from RMA's purchase order's move lines and update the same on RMA picking.
                for move in new_picking.move_ids:
                    demand_qty = move.product_uom_qty
                    rma = new_picking.rma_id
                    purchase_order = rma.purchase_order_id
                    order_line = (
                            purchase_order
                            and purchase_order.order_line.filtered(
                        lambda l: l.product_id.id == move.product_id.id
                    )
                            or False
                    )
                    lot_ids = (
                            order_line
                            and order_line.mapped("move_ids").mapped("lot_ids")
                            or []
                    )
                    if lot_ids:
                        for i in range(0, int(demand_qty)):
                            new_move_line_vals = {
                                "move_id": move.id,
                                "product_id": move.product_id.id,
                                "product_uom": move.product_uom.id,
                                "qty_done": 1,
                                "location_id": move.location_id.id,
                                "location_dest_id": move.location_dest_id.id,
                                "picking_id": move.picking_id.id,
                                "lot_id": lot_ids and lot_ids[i].id or False,
                            }
                            sml = (
                                rma.env["stock.move.line"]
                                .sudo()
                                .create(new_move_line_vals)
                            )
                new_picking.action_confirm()
                new_picking.action_assign()

                # Create invoice vals for refund
                if invoice_vals:
                    inv_values = rma.prepare_invoice_vals(rma, invoice_vals)
                    inv_values.update(
                        {
                            "move_type": "in_refund",
                            "partner_id": rma.supplier_id
                                          and rma.supplier_id.id
                                          or False,
                        }
                    )
                    move = account_move_obj.create(inv_values)
                    move._onchange_partner_id()
                rma.write({"state": state})

            elif rma.rma_type == "invoice":
                moves_vals = []
                invoice_vals = []
                in_domain = [
                    ("warehouse_id.company_id", "in", [rma.company_id.id, False, ],),
                    ("code", "=", "incoming")
                ]
                out_domain = [
                    ("warehouse_id.company_id", "in", [rma.company_id.id, False, ],),
                    ("code", "=", "outgoing")
                ]
                state = "draft"
                for line in rma.rma_inv_lines_ids:
                    state = "approve"
                    # Prepare Move Vals for Delivery Picking
                    rma_move_vals = rma.prepare_stock_move_vals(line, rma)
                    rma_move_vals.update(
                        {"purchase_line_id": False, }
                    )
                    moves_vals.append((0, 0, rma_move_vals))
                    inv_ex_account_id = (
                            line.product_id.property_account_expense_id
                            and line.product_id.property_account_expense_id.id
                            or line.product_id.categ_id.property_account_expense_categ_id
                            and line.product_id.categ_id.property_account_expense_categ_id.id
                            or False
                    )
                    if not inv_ex_account_id:
                        raise ValidationError(
                            ('No account defined for product "%s".')
                            % line.product_id.name
                        )
                    prod_price = 0.0
                    if line.refund_qty != 0:
                        prod_price = float((line.refund_price) / float(line.refund_qty))
                    # PO : Invoice Line vals for Vendor Refund
                    inv_line_vals = rma.prepare_inv_line_vals(line, prod_price, rma)
                    if line.tax_id and line.tax_id.ids:
                        inv_line_vals.update({"tax_ids": [(6, 0, line.tax_id.ids)]})
                    invoice_vals.append((0, 0, inv_line_vals))
                new_picking = False
                for move in moves_vals:
                    picking = stock_picking_obj.search(
                        [
                            ("rma_id", "=", rma.id),
                            ("location_id", "=", move[2].get("location_id")),
                            ("location_dest_id", "=", move[2].get("location_dest_id")),
                        ]
                    )
                    # If no picking found, then create one
                    if not picking:
                        picking_type_id = stock_pick_type_obj.search(
                            out_domain, limit=1
                        ).id

                        picking_re_vals = rma.prepare_picking_vals(
                            picking_type_id, rma, move
                        )
                        picking_re_vals.update(
                            {
                                "partner_id": rma.supplier_id
                                              and rma.supplier_id.id
                                              or False
                            }
                        )
                        picking_rec_re = stock_picking_obj.create(picking_re_vals)
                        new_picking = picking_rec_re
                        picking_rec_re.action_confirm()
                        picking_rec_re.action_assign()
                    else:
                        # If already picking exist, then add move to picking
                        move[2]["picking_id"] = picking.id
                        stock_move_obj.create(move[2])
                        new_picking = picking

                # Get the serial number from RMA's purchase order's move lines and update the same on RMA picking.
                for move in new_picking.move_ids:
                    demand_qty = move.product_uom_qty
                    rma = new_picking.rma_id
                    purchase_order = rma.purchase_order_id
                    order_line = (
                            purchase_order
                            and purchase_order.order_line.filtered(
                        lambda l: l.product_id.id == move.product_id.id
                    )
                            or False
                    )
                    lot_ids = (
                            order_line
                            and order_line.mapped("move_ids").mapped("lot_ids")
                            or []
                    )
                    if lot_ids:
                        for i in range(0, int(demand_qty)):
                            new_move_line_vals = {
                                "move_id": move.id,
                                "product_id": move.product_id.id,
                                "product_uom": move.product_uom.id,
                                "qty_done": 1,
                                "location_id": move.location_id.id,
                                "location_dest_id": move.location_dest_id.id,
                                "picking_id": move.picking_id.id,
                                "lot_id": lot_ids and lot_ids[i].id or False,
                            }
                            sml = (
                                rma.env["stock.move.line"]
                                .sudo()
                                .create(new_move_line_vals)
                            )
                new_picking.action_confirm()
                new_picking.action_assign()
                # Create invoice vals for refund
                if invoice_vals:
                    inv_values = rma.prepare_invoice_vals(rma, invoice_vals)
                    inv_values.update(
                        {
                            "move_type": "in_refund",
                            "partner_id": rma.supplier_id
                                          and rma.supplier_id.id
                                          or False,
                        }
                    )
                    move = account_move_obj.create(inv_values)
                    move._onchange_partner_id()
                rma.write({"state": state})

            elif rma.rma_type == "customer":
                in_domain = [
                    ("warehouse_id.company_id", "in", [rma.sale_order_id.company_id.id, False, ], ),
                    ("code", "=", "incoming")
                ]
                out_domain = [
                    ("warehouse_id.company_id", "in", [rma.sale_order_id.company_id.id, False, ], ),
                    ("code", "=", "outgoing")
                ]
                state = "resolved"
                exchange_move_vals = []
                stock_moves_vals = []
                invoice_line_vals = []
                exchange_inv_line_vals = []
                for rma_line in rma.rma_sale_lines_ids.filtered(lambda x:x.refund_qty > 0):
                    state = "approve"
                    # Prepare Stock Move Vals
                    rma_move_vals_b2b = self.prepare_stock_move_vals(rma_line, rma)
                    stock_moves_vals.append((0, 0, rma_move_vals_b2b))
                    inv_account_id = ''
                    if rma.partner_id and rma.partner_id.journal_id.default_account_id:
                        inv_account_id = rma.partner_id.journal_id.default_account_id.id
                    if not inv_account_id:
                        inv_account_id = (
                            rma_line.product_id.property_account_income_id
                            and rma_line.product_id.property_account_income_id.id
                            or rma_line.product_id.categ_id.property_account_income_categ_id
                            and rma_line.product_id.categ_id.property_account_income_categ_id.id
                            or False
                        )
                    if not inv_account_id:
                        raise ValidationError(
                            ('No account defined for product "%s".')
                            % rma_line.product_id.name
                        )
                    prod_price = 0.0
                    if rma_line.refund_qty != 0:
                        prod_price = float(
                            rma_line.refund_price / float(rma_line.refund_qty)
                        )
                    # Prepare Invoice Line Vals
                    inv_line_values = self.prepare_inv_line_vals(
                        rma_line, prod_price, rma
                    )
                    inv_line_values.update({
                        "account_id": inv_account_id or False,
                        'rma_sale_line_id': rma_line.id or False
                    })
                    if rma_line.tax_id and rma_line.tax_id.ids:
                        inv_line_values.update(
                            {"tax_ids": [(6, 0, rma_line.tax_id.ids)]}
                        )

                    invoice_line_vals.append((0, 0, inv_line_values))
                    # Check if it is exchange
                    if rma_line.type == "exchange":
                        state = "approve"
                        # Prepare move for exchange product
                        rma_move_vals_b2c = self.prepare_exchange_stock_move_vals(
                            rma_line, rma
                        )
                        exchange_move_vals.append((0, 0, rma_move_vals_b2c))
                        # SO : Prepare Invoice Line for Exchange Product
                        inv_line_vals_exchange = self.prepare_exchange_inv_line_vals(
                            rma_line, inv_account_id, rma
                        )
                        inv_line_vals_exchange.update(
                            {"price_unit": rma_line.exchange_product_id.lst_price or 0}
                        )

                        if rma_line.tax_id and rma_line.tax_id.ids:
                            inv_line_vals_exchange.update(
                                {"tax_ids": [(6, 0, rma_line.tax_id.ids)]}
                            )

                        exchange_inv_line_vals.append((0, 0, inv_line_vals_exchange))
                new_picking = False
                # Create Picking or Update move lines in existing pickings
                for move in stock_moves_vals:
                    picking = stock_picking_obj.search(
                        [("rma_id", "=", rma.id),
                         ("location_id", "=", move[2]["location_id"]),
                         ("location_dest_id", "=", move[2]["location_dest_id"]),
                        ]
                    )
                    # If no picking found, then create one
                    if not picking:
                        picking_type_id = stock_pick_type_obj.search(in_domain, limit=1).id

                        picking_vals = self.prepare_picking_vals(picking_type_id, rma, move)
                        picking_vals.update({
                                "partner_id": rma.partner_id
                                and rma.partner_id.id
                                or False
                            })
                        picking_rec = self.env["stock.picking"].create(picking_vals)
                        new_picking = picking_rec
                        new_picking.action_confirm()
                        new_picking.action_assign()

                    else:
                        # If picking already exist, then create its moves
                        move[2]["picking_id"] = picking.id
                        stock_move_obj.create(move[2])
                        new_picking = picking

                # Get the serial number from RMA's sale order's move lines and update the same on RMA picking.
                for move in new_picking.move_ids:
                    demand_qty = move.product_uom_qty
                    rma = new_picking.rma_id
                    sale_order = rma.sale_order_id
                    order_line = (
                        sale_order
                        and sale_order.order_line.filtered(
                            lambda l: l.product_id.id == move.product_id.id
                        )
                        or False
                    )
                    lot_ids = (
                        order_line
                        and order_line.mapped("move_ids").mapped("lot_ids")
                        or []
                    )
                    if lot_ids:
                        for i in range(0, int(demand_qty)):
                            new_move_line_vals = {
                                "move_id": move.id,
                                "product_id": move.product_id.id,
                                "product_uom": move.product_uom.id,
                                "qty_done": 1,
                                "location_id": move.location_id.id,
                                "location_dest_id": move.location_dest_id.id,
                                "picking_id": move.picking_id.id,
                                "lot_id": lot_ids and lot_ids[i].id or False,
                            }
                            sml = (
                                self.env["stock.move.line"]
                                .sudo()
                                .create(new_move_line_vals)
                            )
                new_picking.action_confirm()
                new_picking.action_assign()

                # Check picking for exchange product
                for vals in exchange_move_vals:
                    ex_picking = stock_picking_obj.search(
                        [
                            ("rma_id", "=", rma.id),
                            ("location_id", "=", vals[2]["location_id"]),
                            ("location_dest_id", "=", vals[2]["location_dest_id"]),
                            ("picking_type_code", "=", "outgoing"),
                        ]
                    )
                    if not ex_picking:
                        picking_type = stock_pick_type_obj.search(
                            out_domain, limit=1
                        ).id
                        exchange_picking_vals = self.prepare_picking_vals(
                            picking_type, rma, vals
                        )
                        exchange_picking_vals.update(
                            {
                                "partner_id": rma.partner_id
                                and rma.partner_id.id
                                or False
                            }
                        )
                        picking_rec_ex = stock_picking_obj.create(exchange_picking_vals)
                        picking_rec_ex.action_confirm()
                        picking_rec_ex.action_assign()
                    else:
                        vals[2]["picking_id"] = ex_picking.id
                        stock_move_obj.create(vals[2])
                # SO : Create Credit Note Invoice
                if invoice_line_vals:
                    inv_values = self.prepare_invoice_vals(rma, invoice_line_vals)
                    inv_values.update(
                        {
                            "move_type": "out_refund",
                            "partner_id": rma.partner_id and rma.partner_id.id or False,
                        }
                    )
                    move = account_move_obj.create(inv_values)
                    move._onchange_partner_id()
                # SO : Create Customer Invoice if Exchange Product
                if exchange_inv_line_vals:
                    ex_inv_vals = self.prepare_invoice_vals(rma, exchange_inv_line_vals)
                    ex_inv_vals.update(
                        {
                            "move_type": "out_invoice",
                            "partner_id": rma.partner_id and rma.partner_id.id or False,
                        }
                    )
                    move = account_move_obj.create(ex_inv_vals)
                    move._onchange_partner_id()
                rma.write({"state": state})
            # Check for Purchase Order Return
            elif rma.rma_type == "supplier":
                state = "resolved"
                exchange_moves = []
                moves_vals = []
                invoice_vals = []
                supp_inv_line_vals = []
                in_domain = [
                    ("warehouse_id.company_id", "in", [rma.purchase_order_id.company_id.id, False, ], ),
                    ("code", "=", "incoming")
                ]
                out_domain = [
                    ("warehouse_id.company_id", "in", [rma.purchase_order_id.company_id.id, False, ], ),
                    ("code", "=", "outgoing")
                ]
                for line in rma.rma_purchase_lines_ids:
                    state = "approve"
                    pol = self.env["purchase.order.line"].search(
                        [
                            ("order_id", "=", rma.purchase_order_id.id),
                            ("product_id", "=", line.product_id.id),
                        ]
                    )
                    # Prepare Move Vals for Delivery Picking
                    rma_move_vals = self.prepare_stock_move_vals(line, rma)
                    rma_move_vals.update(
                        {"purchase_line_id": pol[0].id or False,}
                    )
                    moves_vals.append((0, 0, rma_move_vals))
                    inv_ex_account_id = (
                        line.product_id.property_account_expense_id
                        and line.product_id.property_account_expense_id.id
                        or line.product_id.categ_id.property_account_expense_categ_id
                        and line.product_id.categ_id.property_account_expense_categ_id.id
                        or False
                    )
                    if not inv_ex_account_id:
                        raise ValidationError(
                            ('No account defined for product "%s".')
                            % line.product_id.name
                        )
                    prod_price = 0.0
                    if line.refund_qty != 0:
                        prod_price = float((line.refund_price) / float(line.refund_qty))
                    # PO : Invoice Line vals for Vendor Refund
                    inv_line_vals = self.prepare_inv_line_vals(line, prod_price, rma)
                    if line.tax_id and line.tax_id.ids:
                        inv_line_vals.update({"tax_ids": [(6, 0, line.tax_id.ids)]})
                    invoice_vals.append((0, 0, inv_line_vals))
                    if line.type == "exchange":
                        state = "approve"
                        # Prepare the move lines for exchange Moves
                        rma_move_vals_ex = self.prepare_exchange_stock_move_vals(
                            line, rma
                        )
                        rma_move_vals_ex.update({"purchase_line_id": pol.id or False})
                        exchange_moves.append((0, 0, rma_move_vals_ex))
                        supp = self.env["product.supplierinfo"].search(
                            [
                                ("product_id", "=", line.exchange_product_id.id),
                                ("name", "=", rma.supplier_id.id),
                            ]
                        )
                        # Prepare invoice lines for supplier
                        inv_line_vals_supp = self.prepare_exchange_inv_line_vals(
                            line, inv_ex_account_id, rma
                        )
                        inv_line_vals_supp.update({"price_unit": supp.price or 0})
                        if line.tax_id and line.tax_id.ids:
                            inv_line_vals_supp.update(
                                {"tax_ids": [(6, 0, line.tax_id.ids)]}
                            )

                        supp_inv_line_vals.append((0, 0, inv_line_vals_supp))
                new_picking = False
                for move in moves_vals:
                    picking = stock_picking_obj.search(
                        [
                            ("rma_id", "=", rma.id),
                            ("location_id", "=", move[2]["location_id"]),
                            ("location_dest_id", "=", move[2]["location_dest_id"]),
                        ]
                    )
                    # If no picking found, then create one
                    if not picking:
                        picking_type_id = stock_pick_type_obj.search(
                            out_domain, limit=1
                        ).id

                        picking_re_vals = self.prepare_picking_vals(
                            picking_type_id, rma, move
                        )
                        picking_re_vals.update(
                            {
                                "partner_id": rma.supplier_id
                                and rma.supplier_id.id
                                or False
                            }
                        )
                        picking_rec_re = stock_picking_obj.create(picking_re_vals)
                        new_picking = picking_rec_re
                        picking_rec_re.action_confirm()
                        picking_rec_re.action_assign()
                    else:
                        # If already picking exist, then add move to picking
                        move[2]["picking_id"] = picking.id
                        stock_move_obj.create(move[2])
                        new_picking = picking

                # Get the serial number from RMA's purchase order's move lines and update the same on RMA picking.
                for move in new_picking.move_ids:
                    demand_qty = move.product_uom_qty
                    rma = new_picking.rma_id
                    purchase_order = rma.purchase_order_id
                    order_line = (
                        purchase_order
                        and purchase_order.order_line.filtered(
                            lambda l: l.product_id.id == move.product_id.id
                        )
                        or False
                    )
                    lot_ids = (
                        order_line
                        and order_line.mapped("move_ids").mapped("lot_ids")
                        or []
                    )
                    if lot_ids:
                        for i in range(0, int(demand_qty)):
                            new_move_line_vals = {
                                "move_id": move.id,
                                "product_id": move.product_id.id,
                                "product_uom": move.product_uom.id,
                                "qty_done": 1,
                                "location_id": move.location_id.id,
                                "location_dest_id": move.location_dest_id.id,
                                "picking_id": move.picking_id.id,
                                "lot_id": lot_ids and lot_ids[i].id or False,
                            }
                            sml = (
                                self.env["stock.move.line"]
                                .sudo()
                                .create(new_move_line_vals)
                            )
                new_picking.action_confirm()
                new_picking.action_assign()

                for vals in exchange_moves:
                    ex_picking = stock_picking_obj.search(
                        [
                            ("rma_id", "=", rma.id),
                            ("location_id", "=", vals[2]["location_id"]),
                            ("location_dest_id", "=", vals[2]["location_dest_id"]),
                            ("picking_type_code", "=", "incoming"),
                        ]
                    )
                    # Create Picking for exchange product
                    if not ex_picking:
                        picking_type = stock_pick_type_obj.search(in_domain, limit=1).id
                        # Prepare exchange move vals
                        exchange_vals = self.prepare_picking_vals(
                            picking_type, rma, vals
                        )
                        exchange_vals.update(
                            {
                                "partner_id": rma.supplier_id
                                and rma.supplier_id.id
                                or False
                            }
                        )
                        picking_rec_exchange = stock_picking_obj.create(exchange_vals)
                        picking_rec_exchange.action_confirm()
                        picking_rec_exchange.action_assign()
                    else:
                        vals[2]["picking_id"] = ex_picking.id
                        stock_move_obj.create(vals[2])
                # Create invoice vals for refund
                if invoice_vals:
                    inv_values = self.prepare_invoice_vals(rma, invoice_vals)
                    inv_values.update(
                        {
                            "move_type": "in_refund",
                            "partner_id": rma.supplier_id
                            and rma.supplier_id.id
                            or False,
                        }
                    )
                    move = account_move_obj.create(inv_values)
                    move._onchange_partner_id()
                # Create Customer invoice for exchange product
                if supp_inv_line_vals:
                    ex_supp_inv_vals = self.prepare_invoice_vals(
                        rma, supp_inv_line_vals
                    )
                    ex_supp_inv_vals.update(
                        {
                            "move_type": "in_invoice",
                            "partner_id": rma.supplier_id
                            and rma.supplier_id.id
                            or False,
                        }
                    )
                    move = account_move_obj.create(ex_supp_inv_vals)
                    move._onchange_partner_id()
                rma.write({"state": state})
            elif rma.rma_type in ["picking", "lot"]:
                state = "resolved"
                exchange_move_vals = []
                stock_moves_vals = []
                invoice_line_vals = []
                exchange_inv_line_vals = []
                move_type = False
                ex_move_type = False
                lot_id = self.env["stock.lot"].search(
                    [("name", "=", rma.rma_lot)]
                )
                for rma_line in rma.rma_picking_lines_ids:
                    state = "approve"
                    rma_move_vals_b2b = self.prepare_stock_move_vals(rma_line, rma)
                    stock_moves_vals.append((0, 0, rma_move_vals_b2b))
                    inv_account_id = (
                        rma_line.product_id.property_account_income_id
                        and rma_line.product_id.property_account_income_id.id
                        or rma_line.product_id.categ_id.property_account_income_categ_id
                        and rma_line.product_id.categ_id.property_account_income_categ_id.id
                        or False
                    )
                    if not inv_account_id:
                        raise ValidationError(
                            ('No account defined for product "%s".')
                            % rma_line.product_id.name
                        )
                    prod_price = 0.0
                    if rma_line.refund_qty != 0:
                        prod_price = float(
                            (rma_line.refund_price) / float(rma_line.refund_qty)
                        )
                    # Prepare invoice lines
                    inv_line_values = self.prepare_inv_line_vals(
                        rma_line, prod_price, rma
                    )
                    inv_line_values.update(
                        {"account_id": inv_account_id or False,}
                    )

                    if rma_line.tax_id and rma_line.tax_id.ids:
                        inv_line_values.update(
                            {"tax_ids": [(6, 0, rma_line.tax_id.ids)]}
                        )

                    invoice_line_vals.append((0, 0, inv_line_values))
                    if rma_line.type == "exchange":
                        state = "approve"
                        # If rma type is exchange then prepare exchange moves
                        rma_move_vals_b2c = self.prepare_exchange_stock_move_vals(
                            rma_line, rma
                        )
                        exchange_move_vals.append((0, 0, rma_move_vals_b2c))
                        inv_line_vals_exchange = self.prepare_exchange_inv_line_vals(
                            rma_line, inv_account_id, rma
                        )
                        inv_line_vals_exchange.update(
                            {"price_unit": rma_line.exchange_product_id.lst_price or 0}
                        )
                        if rma_line.tax_id and rma_line.tax_id.ids:
                            inv_line_vals_exchange.update(
                                {"tax_ids": [(6, 0, rma_line.tax_id.ids)]}
                            )

                        exchange_inv_line_vals.append((0, 0, inv_line_vals_exchange))

                new_picking = False
                for move in stock_moves_vals:
                    picking = stock_picking_obj.search(
                        [
                            ("rma_id", "=", rma.id),
                            ("location_id", "=", move[2]["location_id"]),
                            ("location_dest_id", "=", move[2]["location_dest_id"]),
                        ]
                    )
                    if not picking:
                        picking_type_id = False
                        pick_partner = False
                        if self.picking_rma_id:
                            pick_partner = self.picking_rma_id.partner_id
                            rma.picking_partner_id = pick_partner
                            if self.picking_rma_id.picking_type_code == "incoming":
                                if self.picking_rma_id.location_id.usage == "supplier":
                                    move_type = "in_refund"
                                if self.picking_rma_id.location_id.usage == "customer":
                                    move_type = "out_invoice"
                                picking_type_id = stock_pick_type_obj.search(
                                    out_domain, limit=1
                                ).id
                            else:
                                if self.picking_rma_id.location_dest_id.usage in [
                                    "supplier",
                                    "transit",
                                ]:
                                    move_type = "in_invoice"
                                if (
                                    self.picking_rma_id.location_dest_id.usage
                                    == "customer"
                                ):
                                    move_type = "out_refund"
                                picking_type_id = stock_pick_type_obj.search(
                                    in_domain, limit=1
                                ).id
                        if self.lot_picking_id:
                            pick_partner = self.lot_picking_id.partner_id
                            rma.picking_partner_id = pick_partner
                            if self.lot_picking_id.picking_type_code == "incoming":
                                if self.lot_picking_id.location_id.usage == "supplier":
                                    move_type = "in_refund"
                                if self.lot_picking_id.location_id.usage == "customer":
                                    move_type = "out_invoice"
                                picking_type_id = stock_pick_type_obj.search(
                                    out_domain, limit=1
                                ).id
                            else:
                                if (
                                    self.lot_picking_id.location_dest_id.usage
                                    == "supplier"
                                ):
                                    move_type = "in_invoice"
                                if (
                                    self.lot_picking_id.location_dest_id.usage
                                    == "customer"
                                ):
                                    move_type = "out_refund"
                                picking_type_id = stock_pick_type_obj.search(
                                    in_domain, limit=1
                                ).id

                        picking_vals = self.prepare_picking_vals(
                            picking_type_id, rma, move
                        )
                        picking_vals.update({"partner_id": pick_partner.id})
                        picking_rec = stock_picking_obj.create(picking_vals)
                        picking_rec.action_confirm()
                        picking_rec.action_assign()
                        new_picking = picking_rec
                        ml = self.env["stock.move.line"].search(
                            [("picking_id", "=", picking_rec.id)]
                        )
                        ml.lot_id = lot_id.id
                        ml.lot_name = lot_id.name
                    else:
                        move[2]["picking_id"] = picking.id
                        stock_move_obj.create(move[2])
                        new_picking = picking
                        if picking.location_dest_id.usage == "supplier":
                            move_type = "in_invoice"
                        elif picking.location_dest_id.usage == "customer":
                            move_type = "out_refund"
                        elif picking.location_id.usage == "supplier":
                            move_type = "in_invoice"
                        elif picking.location_id.usage == "customer":
                            move_type = "out_refund"

                if self.picking_rma_id:
                    # Get the serial number from RMA's picking's move lines and update the same on RMA picking.
                    for move in new_picking.move_ids:
                        demand_qty = move.product_uom_qty
                        rma = new_picking.rma_id
                        picking_order = rma.picking_rma_id
                        pick_move_line = (
                            picking_order
                            and picking_order.move_ids.filtered(
                                lambda l: l.product_id.id == move.product_id.id
                            )
                            or False
                        )
                        lot_ids = (
                            pick_move_line and pick_move_line.mapped("lot_ids") or []
                        )
                        if lot_ids:
                            for i in range(0, int(demand_qty)):
                                new_move_line_vals = {
                                    "move_id": move.id,
                                    "product_id": move.product_id.id,
                                    "product_uom": move.product_uom.id,
                                    "qty_done": 1,
                                    "location_id": move.location_id.id,
                                    "location_dest_id": move.location_dest_id.id,
                                    "picking_id": move.picking_id.id,
                                    "lot_id": lot_ids and lot_ids[i].id or False,
                                }
                                sml = (
                                    self.env["stock.move.line"]
                                    .sudo()
                                    .create(new_move_line_vals)
                                )
                    new_picking.action_confirm()
                    new_picking.action_assign()

                for vals in exchange_move_vals:
                    ex_picking = stock_picking_obj.search(
                        [
                            ("rma_id", "=", rma.id),
                            ("location_id", "=", vals[2]["location_id"]),
                            ("location_dest_id", "=", vals[2]["location_dest_id"]),
                            ("picking_type_code", "=", "outgoing"),
                        ]
                    )
                    if not ex_picking:
                        picking_type = False
                        pick_partner = False
                        if self.picking_rma_id:
                            pick_partner = self.picking_rma_id.partner_id
                            rma.picking_partner_id = pick_partner
                            if self.picking_rma_id.picking_type_code == "incoming":
                                if self.picking_rma_id.location_id.usage == "supplier":
                                    ex_move_type = "in_invoice"
                                if self.picking_rma_id.location_id.usage == "customer":
                                    ex_move_type = "out_refund"
                                picking_type = stock_pick_type_obj.search(
                                    in_domain, limit=1
                                ).id
                            else:
                                if (
                                    self.picking_rma_id.location_dest_id.usage
                                    == "supplier"
                                ):
                                    ex_move_type = "in_refund"
                                if (
                                    self.picking_rma_id.location_dest_id.usage
                                    == "customer"
                                ):
                                    ex_move_type = "out_invoice"
                                picking_type = stock_pick_type_obj.search(
                                    out_domain, limit=1
                                ).id
                        if self.lot_picking_id:
                            pick_partner = self.lot_picking_id.partner_id
                            rma.picking_partner_id = pick_partner
                            if self.lot_picking_id.picking_type_code == "incoming":
                                if self.lot_picking_id.location_id.usage == "supplier":
                                    ex_move_type = "in_invoice"
                                if self.lot_picking_id.location_id.usage == "customer":
                                    ex_move_type = "out_refund"
                                picking_type = stock_pick_type_obj.search(
                                    in_domain, limit=1
                                ).id
                            else:
                                if (
                                    self.lot_picking_id.location_dest_id.usage
                                    == "supplier"
                                ):
                                    ex_move_type = "in_refund"
                                if (
                                    self.lot_picking_id.location_dest_id.usage
                                    == "customer"
                                ):
                                    ex_move_type = "out_invoice"
                                picking_type = stock_pick_type_obj.search(
                                    out_domain, limit=1
                                ).id
                        exchange_picking_vals = self.prepare_picking_vals(
                            picking_type, rma, vals
                        )
                        exchange_picking_vals.update({"partner_id": pick_partner.id})
                        picking_rec_ex = stock_picking_obj.create(exchange_picking_vals)
                        picking_rec_ex.action_confirm()
                        picking_rec_ex.action_assign()
                    else:
                        vals[2]["picking_id"] = ex_picking.id
                        stock_move_obj.create(vals[2])
                        if ex_picking.location_dest_id.usage == "supplier":
                            move_type = "in_invoice"
                        elif ex_picking.location_dest_id.usage == "customer":
                            move_type = "out_refund"
                        elif ex_picking.location_id.usage == "supplier":
                            move_type = "in_invoice"
                        elif ex_picking.location_id.usage == "customer":
                            move_type = "out_refund"
                if invoice_line_vals:
                    inv_values = self.prepare_invoice_vals(rma, invoice_line_vals)
                    inv_values.update(
                        {
                            "move_type": move_type,
                            "partner_id": rma.picking_partner_id
                            and rma.picking_partner_id.id
                            or rma.picking_rma_id.partner_id.id
                            or False,
                        }
                    )
                    move = account_move_obj.create(inv_values)
                    move._onchange_partner_id()
                if exchange_inv_line_vals:
                    ex_inv_vals = self.prepare_invoice_vals(rma, exchange_inv_line_vals)
                    ex_inv_vals.update(
                        {
                            "move_type": ex_move_type,
                            "partner_id": rma.picking_partner_id
                            and rma.picking_partner_id.id
                            or rma.picking_rma_id.partner_id.id
                            or False,
                        }
                    )
                    move = account_move_obj.create(ex_inv_vals)
                    move._onchange_partner_id()
                rma.write({"state": state})
            return True

    def count_stock_picking(self):
        """
            Counting the number of pickings.
            Redirect to Picking Views.
        """
        for rec in self:
            picview_id = self.env.ref("stock.view_picking_form")
            picking_ids = self.env["stock.picking"].search([("rma_id", "=", rec.id)])
            if len(picking_ids.ids) > 1:
                return {
                    "name": "Stock Pickings",
                    "view_type": "form",
                    "view_mode": "list,form",
                    "view_id": False,
                    "res_model": "stock.picking",
                    "type": "ir.actions.act_window",
                    "target": "current",
                    "domain": [("id", "in", picking_ids.ids)],
                    "context": {"show_lots_m2o": True},
                }
            elif len(picking_ids.ids) == 1:
                return {
                    "name": "Stock picking",
                    "view_type": "form",
                    "view_mode": "form",
                    "view_id": picview_id.id,
                    "res_model": "stock.picking",
                    "type": "ir.actions.act_window",
                    "target": "current",
                    "res_id": picking_ids[0].id,
                    "context": {"show_lots_m2o": True},
                }

    def count_invoice_ids(self):
        """
            Counting the number of invoice created from RMA.
            Redirect to invoice form view and tree views based on count.
        """
        for rec in self:
            if rec.rma_type in ["customer", "sale_direct"]:
                action = self.env["ir.actions.actions"]._for_xml_id(
                    "account.action_move_out_refund_type"
                )
            elif rec.rma_type in ["supplier", "direct", "picking", "lot", "invoice"]:
                action = self.env["ir.actions.actions"]._for_xml_id(
                    "account.action_move_in_refund_type"
                )
            else:
                 action = {"type": "ir.actions.act_window_close"}
            
            invoice_ids = self.env["account.move"].search([("rma_id", "=", rec.id)])
            if len(invoice_ids.ids) > 1:
                action["domain"] = [("id", "in", invoice_ids.ids)]
            elif len(invoice_ids.ids) == 1:
                if rec.rma_type in ["customer", "supplier", "direct", "invoice", "sale_direct"]:
                    action["views"] = [
                        (self.env.ref("account.view_move_form").id, "form")
                    ]

                if rec.picking_rma_id.picking_type_id.code in ["incoming", "outgoing"]:
                    action["views"] = [
                        (self.env.ref("account.view_move_form").id, "form")
                    ]

                if rec.lot_picking_id.picking_type_id.code in ["incoming", "outgoing"]:
                    action["views"] = [
                        (self.env.ref("account.view_move_form").id, "form")
                    ]

                action["res_id"] = invoice_ids[0].id
            else:
                action = {"type": "ir.actions.act_window_close"}
            return action

    def unlink(self):
        """
            Before deleting rma, check its status
        """
        if self.filtered(lambda r: r.state in ["close", "approve"]):
            raise ValidationError(
                _(
                    "You can not delete Approved or \
Done RMA."
                )
            )
        return super(RMARetMerAuth, self).unlink()

    @api.onchange("sale_order_id")
    def _onchange_sale_order_id(self):
        """
            On selecting sale order auto populate data to lines from sale lines
        """
        order_line_lst = []
        for order_line in self.sale_order_id.order_line:
            rma_sale_line = (
                0,
                0,
                {
                    "product_id": order_line.product_id
                    and order_line.product_id.id
                    or False,
                    "total_qty": order_line.product_uom_qty or 0,
                    "delivered_quantity": order_line.qty_delivered,
                    "order_quantity": order_line.product_uom_qty or 0,
                    "refund_qty": order_line.qty_delivered,
                    "refund_price": order_line.price_unit * order_line.qty_delivered,
                    "price_unit": order_line.price_unit or 0,
                    "price_subtotal": order_line.price_subtotal or 0,
                    "source_location_id": self.sale_order_id.company_id.source_location_id.id
                    or False,
                    "destination_location_id": self.sale_order_id.company_id.destination_location_id.id
                    or False,
                    "type": "return",
                    "tax_id": order_line.tax_ids,
                    "discount": order_line.discount,
                    "analytic_account_id": self.sale_order_id.analytic_account_id.id or False,
                },
            )
            order_line_lst.append(rma_sale_line)
        self.rma_sale_lines_ids = [(5,)]
        self.rma_sale_lines_ids = order_line_lst

    @api.onchange("picking_rma_id")
    def _onchange_picking_rma_id(self):
        """
            On selection of picking auto add lines from stock moves
        """
        order_line_lst = []
        for order_line in self.picking_rma_id.move_ids:
            move = self.env["stock.move"].search(
                [
                    ("picking_id", "=", self.picking_rma_id.id),
                    ("product_id", "=", order_line.product_id.id),
                ]
            )
            so_line = self.env["rma.sale.lines"].search(
                [
                    ("product_id", "=", order_line.product_id.id),
                    ("rma_id", "=", self.picking_rma_id.rma_id.id),
                ]
            )
            taxes = []
            domain = [
                ("exchange_product_id", "=", order_line.product_id.id),
                ("rma_id", "=", move.rma_id.id),
            ]
            if move.picking_id.rma_id.rma_type == "customer":
                line = self.env["rma.sale.lines"].search(domain)
                taxes = line.tax_id
            if move.picking_id.rma_id.rma_type == "supplier":
                line = self.env["rma.purchase.lines"].search(domain)
                taxes = line.tax_id

            # Fetch the correct product price from previous RMA.
            product_price = 1
            product_tax = []
            if self.picking_rma_id and self.pick_origin:
                prev_rma = self.search([("name", "=", self.pick_origin)], limit=1)
                if prev_rma.rma_type == "customer":
                    rma_line = prev_rma.rma_sale_lines_ids.filtered(
                        lambda l: l.product_id == order_line.product_id
                    )
                    if rma_line:
                        product_price = rma_line[0].price_unit
                        product_tax = rma_line[0].tax_id.ids
                if prev_rma.rma_type == "supplier":
                    rma_line = prev_rma.rma_purchase_lines_ids.filtered(
                        lambda l: l.product_id == order_line.product_id
                    )
                    if rma_line:
                        product_price = rma_line[0].price_unit
                        product_tax = rma_line[0].tax_id.ids
                if prev_rma.rma_type == "picking":
                    rma_line = prev_rma.rma_picking_lines_ids.filtered(
                        lambda l: l.product_id == order_line.product_id
                    )
                    if rma_line:
                        product_price = rma_line[0].price_unit
                        product_tax = rma_line[0].tax_id.ids

            rma_pick_line = {
                "product_id": order_line.product_id
                and order_line.product_id.id
                or False,
                "total_qty": order_line.quantity or 0,
                "delivered_quantity": order_line.quantity,
                "order_quantity": order_line.product_uom_qty or 0,
                "refund_qty": order_line.quantity,
                "refund_price": product_price * order_line.quantity,
                "price_unit": product_price or 0,
                "source_location_id": self.picking_rma_id.location_id.id or False,
                "destination_location_id": self.picking_rma_id.location_dest_id.id
                or False,
                "type": "return",
                "tax_id": product_tax or False,
            }
            if self.picking_rma_id.picking_type_id.code == "incoming" and so_line:
                rma_pick_line.update({"discount": so_line.discount or 0.0})
            order_line_lst.append((0, 0, rma_pick_line))
        self.rma_picking_lines_ids = [(5,)]
        self.rma_picking_lines_ids = order_line_lst

    @api.onchange("lot_picking_id")
    def _onchange_lot_picking_id(self):
        """
            Based on lot find it's picking and from picking auto add lines
        """
        order_line_lst = []
        for order_line in self.lot_picking_id.move_ids:
            mls = self.env["stock.move.line"].search([("move_id", "=", order_line.id)])
            qty = 0
            lot_no = self.env["stock.production.lot"].search(
                [("name", "=", self.rma_lot)]
            )
            if lot_no:
                ml = mls.filtered(lambda r: r.lot_id == lot_no)
                # If no ml, qty will be zero, and it will raise warning 'Refund qty should be greater than zero'.
                # So skip, if no ml.
                if not ml:
                    continue
                qty = ml.qty_done
            move = self.env["stock.move"].search(
                [
                    ("picking_id", "=", self.picking_rma_id.id),
                    ("product_id", "=", order_line.product_id.id),
                ]
            )
            taxes = []
            domain = [
                ("product_id", "=", order_line.product_id.id),
                ("rma_id", "=", move.rma_id.id),
            ]
            if move.picking_id.rma_id.rma_type == "customer":
                line = self.env["rma.sale.lines"].search(domain)
                taxes = line.tax_id
            if move.picking_id.rma_id.rma_type == "supplier":
                line = self.env["rma.purchase.lines"].search(domain)
                taxes = line.tax_id

            # Fetch the correct product price & taxes from the linked SO, PO, or previous RMA.
            product_price = 1
            product_tax = []
            if self.lot_picking_id:
                if self.lot_picking_id.group_id.sale_id:
                    sale_order = self.env["sale.order"].browse(
                        self.lot_picking_id.group_id.sale_id.id
                    )
                    sale_line = sale_order.order_line.filtered(
                        lambda l: l.product_id == order_line.product_id
                    )
                    if sale_line:
                        product_price = sale_line[0].price_unit
                        product_tax = sale_line[0].tax_id.ids
                elif (
                    not self.lot_picking_id.group_id.sale_id
                    and self.lot_picking_id.group_id
                ):
                    purchase_order = self.env["purchase.order"].search(
                        [("name", "=", self.lot_picking_id.group_id.name)], limit=1
                    )
                    po_line = purchase_order.order_line.filtered(
                        lambda l: l.product_id == order_line.product_id
                    )
                    if po_line:
                        product_price = po_line[0].price_unit
                        product_tax = po_line[0].taxes_id.ids
                elif not self.lot_picking_id.group_id:
                    prev_rma = self.search(
                        [("name", "=", self.lot_picking_id.origin)], limit=1
                    )
                    if prev_rma.rma_type == "lot":
                        product_line = prev_rma.rma_picking_lines_ids.filtered(
                            lambda l: l.product_id == order_line.product_id
                        )
                        if product_line:
                            product_price = product_line[0].price_unit
                            product_tax = product_line[0].tax_id.ids

            rma_pick_line = (
                0,
                0,
                {
                    "product_id": order_line.product_id
                    and order_line.product_id.id
                    or False,
                    "total_qty": qty,
                    "delivered_quantity": qty,
                    "order_quantity": qty,
                    "refund_qty": qty,
                    "refund_price": product_price,
                    "price_unit": product_price or 0,
                    "source_location_id": self.lot_picking_id.location_id.id or False,
                    "destination_location_id": self.lot_picking_id.location_dest_id.id
                    or self.env.user.company_id.destination_location_id.id
                    or False,
                    "type": "return",
                    "tax_id": product_tax or False,
                },
            )
            order_line_lst.append(rma_pick_line)
        self.rma_picking_lines_ids = [(5,)]
        self.rma_picking_lines_ids = order_line_lst

    @api.onchange("purchase_order_id")
    def _onchange_purchase_order_id(self):
        """
            Onchange of purchase order it will auto-populate lines from
            purchase order lines
        """
        po_line_lst = []
        for order_line in self.purchase_order_id.order_line:
            rma_purchase_line = (
                0,
                0,
                {
                    "product_id": order_line.product_id
                    and order_line.product_id.id
                    or False,
                    "total_qty": order_line.product_uom_qty or 0,
                    "refund_qty": order_line.qty_received or 0,
                    "refund_price": order_line.price_unit * order_line.qty_received,
                    "order_quantity": order_line.qty_received or 0,
                    "delivered_quantity": order_line.qty_received,
                    "total_price": order_line.price_total,
                    "price_unit": order_line.price_unit or 0,
                    "source_location_id": self.purchase_order_id.company_id.sup_source_location_id.id
                    or False,
                    "destination_location_id": self.purchase_order_id.company_id.sup_destination_location_id.id
                    or False,
                    "type": "return",
                    "tax_id": order_line.tax_ids,
                },
            )
            po_line_lst.append(rma_purchase_line)
        self.rma_purchase_lines_ids = [(5,)]
        self.rma_purchase_lines_ids = po_line_lst


    def action_get_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale',
            'views': [(False, 'form')],
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'domain': [('rma_ids', 'in', self.ids)],
            'target': 'current',
            'context': {'create': False, 'delete': False},
        }

    so_lines_created = fields.Boolean(default=False)

    # def action_get_linked_pickings(self):
    #     return {
    #         "name": "Related Pickings",
    #         "type": "ir.actions.act_window",
    #         "res_model": "stock.picking",
    #         "view_mode": "list,form",
    #         "domain": [("id", "in", self.picking_ids.ids)],
    #     }


    def create_so_lines(self):
        self.ensure_one()
        wiz_lines = []
        for line in self.rma_sale_lines_ids:
            wiz_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.refund_qty,
                'price_unit': line.price_unit,
            }))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Create SO Line'),
            'res_model': 'create.so.line.wiz',
            'target': 'new',
            'view_mode': 'form',
            'context': {
                'default_rma_id': self.id,
                'default_sale_id': self.sale_order_id.id,
                'default_wiz_line_ids': wiz_lines,
            },
        }