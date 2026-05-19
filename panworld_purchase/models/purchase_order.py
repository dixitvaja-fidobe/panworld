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


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    presale_original_name = fields.Char(string='Original Sequence', readonly=True, copy=False)
    po_total = fields.Float(
        string='PO Total',
        required=False,
        compute="_compute_po_total",
        store=True,
    )
    po_pending_qty = fields.Integer(string='Pending Qty', compute='_compute_po_pending_qty_and_status', store=True)
    po_status = fields.Selection([("closed", "Closed"), ("open", "Open")],
                                 string="PO Status", compute='_compute_po_pending_qty_and_status', store=True)

    # po_pending_qty = fields.Integer(string='Pending Qty', store=True)
    # po_status = fields.Selection([("closed", "Closed"), ("open", "Open")],
    #                              string="PO Status", store=True)
    carrier_id = fields.Many2one(
        "delivery.carrier",
        string="Delivery Method",
        # domain="[('carrier_type','=','purchase'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Fill this field if you plan to invoice the shipping based on picking.",
    )
    target_weight = fields.Float(related='carrier_id.target_weight', string="Target Weight", store=True)
    delivery_set = fields.Boolean(compute="_compute_delivery_state")
    is_all_service = fields.Boolean(
        "Service Product", compute="_compute_is_service_products"
    )
    recompute_delivery_price = fields.Boolean("Delivery cost should be recomputed")
    additional_po_service_ids = fields.One2many(
        "additional.purchase.order.lines", "order_id", "Additional Services"
    )
    company_currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", string="Company Currency"
    )
    total_additional_amount = fields.Monetary(
        compute="_compute_additional_amount",
        string="Shipment Estimation",
        currency_field="company_currency_id",
        help="Amount in Company Currency",
        compute_sudo=True,
    )
    total_additional_amount_order_currency = fields.Monetary(
        compute="_compute_additional_amount",
        help="Amount in Order Currency",
        compute_sudo=True,
    )
    total_estimated_cost = fields.Monetary(compute="_compute_total_est_cost")
    total_order_quantity = fields.Integer(
        compute="_compute_total_order_quantity", string='Total Order Quantity')
    customer_sales_order = fields.Char(string='Customer Sales Order')
    customer_so_date = fields.Date(string='Customer Sales Order Date')
    carrier_tracking_ref = fields.Char(string='Tracking(AWB)')
    picking_ids = fields.Many2many(
        "stock.picking",
        compute="_compute_picking_ids",
        string="Receptions",
        copy=False,
        store=True,
    )
    shipping_option_id = fields.Many2one(
        "purchase.shipping.options.rule",
        "Shipping Options",
        domain="[('company_id', '=', current_company_id)]",
        default=lambda self: self.env["purchase.shipping.options.rule"].search(
            [("default_option", "=", True)], limit=1
        ),
        help="Select Shipping options Direct ship or via shipper",
    )
    total_weight = fields.Float(compute="_compute_total_weight")
    consolidated_weight = fields.Float("Consolidated Weight", copy=False)
    consolidated_weight_uom = fields.Char(
        string="Consolidated Weight unit of measure label",
        compute="_compute_weight_uom_name",
        readonly=True,
    )
    weight_uom_name = fields.Char(
        string="Weight unit of measure label",
        compute="_compute_weight_uom_name",
        readonly=True,
    )
    is_carrier_tracking_required = fields.Boolean("Is Carrier Tracking Required")
    shipping_location_id = fields.Many2one("res.partner", string="Deliver To",
                                           default=lambda self: self.env.company.partner_id)
    publisher_id = fields.Many2one(
        comodel_name="res.partner",
        string="Publisher",
        domain=lambda self: "[('category_id', 'in', %s)]"
                            % [self.env.ref("panworld_contact.res_partner_category_publisher").id],
    )
    is_service_quotation = fields.Boolean(string='Service Quotation')

    @api.depends("order_line")
    def _compute_delivery_state(self):
        for order in self:
            order.delivery_set = any(
                order.carrier_id.product_id == line.product_id
                for line in order.additional_po_service_ids
            )

    @api.depends("additional_po_service_ids")
    def _compute_additional_amount(self):
        for rec in self:
            additional_amount = sum(
                rec.additional_po_service_ids.mapped("price_subtotal")
            )
            rec.total_additional_amount = additional_amount
            rec.total_additional_amount_order_currency = (
                    additional_amount * rec.currency_rate
            )

    @api.depends("total_additional_amount", "amount_total")
    def _compute_total_est_cost(self):
        for rec in self:
            rec.total_estimated_cost = (
                    rec.total_additional_amount_order_currency + rec.amount_total
            )

    @api.depends("order_line.product_qty")
    def _compute_total_order_quantity(self):
        # Get total order product quantity.
        for rec in self:
            rec.total_order_quantity = sum(
                line.product_qty for line in rec.order_line)

    @api.onchange("carrier_id")
    def _onchange_carrier_id(self):
        self.shipping_option_id = self.carrier_id.shipping_option_id.id

    @api.onchange("partner_id", "company_id")
    def onchange_partner_id(self):
        res = super().onchange_partner_id()
        self.carrier_id = False
        if self.partner_id.country_id:
            carrier_id = self.env["delivery.carrier"].search([
                ("country_ids", "in", self.partner_id.country_id.ids),
                ("carrier_type", "=", "purchase"),
                ("company_id", "=", self.env.company.id)
            ], limit=1)
            if carrier_id:
                self.update({"carrier_id": carrier_id.id})
        return res

    def _prepare_picking(self):
        res = super()._prepare_picking()
        res.update({"carrier_id": self.carrier_id.id or False})
        return res

    @api.depends("order_line")
    def _compute_is_service_products(self):
        for po in self:
            po.is_all_service = all(
                line.product_id.type == "service"
                for line in po.order_line.filtered(lambda x: not x.display_type)
            )

    def _compute_amount_total_without_delivery(self):
        for rec in self:
            delivery_cost = sum(rec.order_line.mapped("price_total"))
            return rec.amount_total - delivery_cost

    def set_purchase_delivery_line(self, carrier, amount, delivery_weight, consolidated_weight):
        for order in self:
            order.carrier_id = carrier.id
            order._purchase_create_delivery_line(
                carrier, amount, delivery_weight, consolidated_weight
            )
        return True

    def _prepare_additional_service_lines(self, carrier):
        service_lines = []
        for line in carrier.additional_service_ids:
            # Apply fiscal position
            taxes = line.product_id.taxes_id.filtered(
                lambda t: t.company_id == self.company_id
            )
            taxes_ids = taxes.ids
            if self.partner_id and self.fiscal_position_id:
                taxes_ids = self.fiscal_position_id.map_tax(taxes).ids

            unit_price = line.price_unit
            if (
                    self.consolidated_weight > 0
                    and line.product_id.split_method_landed_cost == "by_weight"
            ):
                unit_price = (unit_price * self.total_weight) / self.consolidated_weight
            values = {
                "order_id": self.id,
                "product_id": line.product_id.id,
                "name": line.product_id.display_name,
                "product_qty": line.product_qty,
                "product_uom": line.product_id.uom_id.id,
                "consolidated_price": line.price_unit,
                "price_unit": unit_price,
                "taxes_id": [(6, 0, taxes_ids)],
            }
            service_lines.append(values)
        return service_lines

    def _purchase_create_delivery_line(self, carrier, price_unit, delivery_weight, consolidated_weight):
        AdditionalPurchaseLines = self.env["additional.purchase.order.lines"]
        # Remove Existing Lines
        self.additional_po_service_ids = [(5,)]
        context = {}
        if self.partner_id:
            # set delivery detail in the customer language
            context["lang"] = self.partner_id.lang
            carrier = carrier.with_context(lang=self.partner_id.lang)

            # Apply fiscal position
        taxes = carrier.product_id.taxes_id.filtered(
            lambda t: t.company_id == self.company_id
        )
        taxes_ids = taxes.ids
        if self.partner_id and self.fiscal_position_id:
            taxes_ids = self.fiscal_position_id.map_tax(taxes).ids

        # Create the sales order line

        if carrier.product_id.description_sale:
            so_description = "{}: {}".format(
                carrier.name, carrier.product_id.description_sale
            )
        else:
            so_description = carrier.name
        values = {
            "order_id": self.id,
            "name": so_description,
            "product_qty": delivery_weight,
            "product_uom": carrier.product_id.uom_id.id,
            "consolidated_price": consolidated_weight * price_unit,
            "product_id": carrier.product_id.id,
            "taxes_id": [(6, 0, taxes_ids)],
        }
        if carrier.invoice_policy == "real":
            values["price_unit"] = 0
            values["name"] += _(
                " (Estimated Cost: %s )", self._format_currency_amount(price_unit)
            )
        else:
            values["price_unit"] = price_unit
        if carrier.free_over and self.currency_id.is_zero(price_unit):
            values["name"] += "\n" + _("Free Shipping")
        service_lines = self._prepare_additional_service_lines(carrier)
        service_lines.append(values)

        pol = AdditionalPurchaseLines.sudo().create(service_lines)
        return pol

    @api.depends('order_line.rfq_qty', 'order_line.cancel_qty', 'order_line.qty_received')
    def _compute_po_pending_qty_and_status(self):
        for order in self:
            rfq_qty = sum(order.order_line.mapped('rfq_qty'))
            qty_received = sum(order.order_line.mapped('qty_received'))
            cancel_qty = sum(order.order_line.mapped('cancel_qty'))
            po_pending_qty = (rfq_qty - qty_received) - cancel_qty
            order.po_pending_qty = po_pending_qty
            if order.state in ['purchase', 'done', 'cancel']:
                if order.po_pending_qty == 0:
                    order.po_status = 'closed'
                else:
                    order.po_status = 'open'
            else:
                order.po_status = 'open'

    # def button_confirm(self):
    #     res = super(PurchaseOrder, self).button_confirm()
    #     # if self.picking_type_id.code == 'incoming' and self.picking_type_id.default_location_dest_id.usage != 'transit' and not self.picking_type_id.default_location_dest_id.is_shipper_location:
    #     if self.picking_type_id.code == 'internal' and self.picking_type_id.default_location_dest_id.usage != 'transit' and not self.picking_type_id.default_location_dest_id.is_shipper_location:
    #         sml = self.picking_ids.filtered(lambda l: l.state == 'assigned').move_line_ids
    #         for sml in sml:
    #             sml.qty_done = sml.move_id.purchase_line_id.to_be_received_qty
    #     return res

    def button_confirm(self):
        # Restore original sequence if set
        for order in self:
            if order.presale_original_name:
                order.name = order.presale_original_name
        res = super(PurchaseOrder, self).button_confirm()
        for rec in self:
            rec.picking_ids.sudo().write(
                {
                    "consolidated_weight": rec.consolidated_weight,
                    "carrier_tracking_ref": rec.carrier_tracking_ref,
                }
            )
            # Automatically reserve pickings created from PO (move to 'Ready' state)
            pickings = rec.picking_ids.filtered(lambda p: p.state in ('waiting', 'confirmed'))
            if pickings:
                pickings.action_assign()
                # Ensure Done quantity remains zero after reservation
                for picking in pickings:
                    picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')).write({
                        'picked': False
                    })
        return res

    @api.depends(
        "order_line.po_subtotal",
    )
    def _compute_po_total(self):
        for rec in self:
            rec.po_total = sum(rec.order_line.filtered(lambda l: not l.display_type).mapped('po_subtotal') or [0])

    @api.depends('po_total')
    def _compute_tax_totals(self):
        """Override to add po_total to the tax_totals JSON structure"""
        res = super()._compute_tax_totals()
        for order in self:
            if order.tax_totals:
                order.tax_totals['po_total'] = order.po_total
        return res

    # @api.depends(
    #     "order_line.move_ids.returned_move_ids",
    #     "order_line.move_ids.state",
    #     "order_line.move_ids.picking_id",
    # )
    # def _compute_picking_ids(self):
    #     for order in self:
    #         pickings = self.env["stock.picking"]
    #         for line in order.order_line:
    #             # We keep a limited scope on purpose. Ideally, we should also
    #             # use move_orig_ids and do some recursive search, but that
    #             # could be prohibitive if not done correctly.
    #             moves = line.move_ids | line.move_ids.mapped("returned_move_ids")
    #             pickings |= moves.mapped("picking_id")
    #         moves_with_po_origin = self.env["stock.move"].search(
    #             [("origin", "=", order.name)]
    #         )
    #         origin_move_pickings = moves_with_po_origin.mapped("picking_id")
    #         other_pickings = pickings.search([("origin", "=", order.name)])
    #         internal_picks = pickings.search(
    #             [("origin", "in", other_pickings.mapped("name"))]
    #         )
    #         pickings |= (
    #             other_pickings | other_pickings | internal_picks | origin_move_pickings
    #         )
    #         order.picking_ids = pickings

    @api.depends("order_line.product_id")
    def _compute_total_weight(self):
        for rec in self:
            rec.total_weight = sum(
                line.product_id.weight * line.product_qty for line in rec.order_line)

    def _compute_weight_uom_name(self):
        """ Get the unit of measure to interpret the `weight` field. By default, we considerer
        that weights are expressed in kilograms. Users can configure to express them in pounds
        by adding an ir.config_parameter record with "product.product_weight_in_lbs" as key
        and "1" as value.
        """
        for rec in self:
            rec.consolidated_weight_uom = rec.weight_uom_name = self.env[
                "product.template"
            ]._get_weight_uom_name_from_ir_config_parameter()

    def _prepare_picking(self):
        res = super()._prepare_picking()
        res.update({
            'customer_sales_order': self.customer_sales_order or '',
            'is_carrier_tracking_required': self.is_carrier_tracking_required
        })
        if self.shipping_option_id.is_grn_tracking:
            res.update({
                'carrier_tracking_ref': self.carrier_tracking_ref or ''
            })
        return res

    @api.onchange("shipping_option_id")
    def _onchange_shipping_option_id(self):
        """Onchange Method to set operation type form shipping option"""
        self.picking_type_id = self.shipping_option_id.picking_type_id.id
        self.is_carrier_tracking_required = False
        if self.shipping_option_id.is_grn_tracking:
            self.is_carrier_tracking_required = True

    def create_purchase_return(self):
        """Create return of purchase and redirect to RMA."""
        ctx = self.env.context.copy()
        ctx.update(
            {
                "from_purchase_return": True,
                "default_rma_type": "supplier",
                "default_supplier_id": self.partner_id.id,
                "default_purchase_order_id": self.id,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "rma.ret.mer.auth",
            "view_mode": "form",
            "context": ctx,
            "name": "Return",
        }

    def action_create_invoice(self, attachment_ids=False):
        """Overwrite method to pass grn and po number when
        Create the invoice associated to the PO.
        """
        # Shows Warning to Update the to be received qty in Shipper Receipt.
        for order in self:
            if order.picking_type_id.code == 'internal' and order.picking_type_id.default_location_dest_id.usage == 'transit' and order.picking_type_id.default_location_dest_id.is_shipper_location:
                picking_ids = order.picking_ids.filtered(lambda l: l.state not in ('cancel'))
                move_ids_done_record = picking_ids.move_ids.filtered(lambda
                                                                                         x: x.state == 'done' and x.purchase_line_id.to_be_received_qty == x.quantity and x.purchase_line_id.product_id.id == x.product_id.id)
                # move_ids_not_done_record = picking_ids.move_ids.filtered(lambda
                #                                                                              x: x.state != 'done' and x.purchase_line_id.to_be_received_qty != x.quantity and x.purchase_line_id.product_id.id == x.product_id.id)
                if move_ids_done_record:
                    for rec in move_ids_done_record:
                        rec.purchase_line_id._prepare_account_move_line()

        precision = self.env['decimal.precision'].precision_get('Product Unit')
        # 1) Prepare invoice vals and clean-up the section lines
        invoice_vals_list = []
        sequence = 10
        for order in self:
            if order.invoice_status != 'to invoice':
                continue

            order = order.with_company(order.company_id)
            pending_section = None
            # Invoice values.
            invoice_vals = order._prepare_invoice()
            # Invoice line values (keep only necessary sections).
            for line in order.order_line:
                if line.display_type in ('line_section', 'line_subsection'):
                    pending_section = line
                    continue
                if not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    if pending_section:
                        invoice_vals['invoice_line_ids'].append((0, 0, pending_section._prepare_account_move_line()))
                        pending_section = None
                    invoice_vals['invoice_line_ids'].append((0, 0, line._prepare_account_move_line()))
            invoice_vals['is_service_quotation'] = order.is_service_quotation
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(_('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))

        # 2) group by (company_id, partner_id, currency_id) for batch creation
        new_invoice_vals_list = []
        for _grouping_keys, invoices in groupby(invoice_vals_list,
                                                key=lambda x: (x.get('company_id'), x.get('partner_id'),
                                                               x.get('currency_id'))):
            origins = set()
            payment_refs = set()
            refs = []
            grn_tracking = []
            tracking_ref = []
            ref_invoice_vals = None
            is_service_quotation = False
            for invoice_vals in invoices:
                if not ref_invoice_vals:
                    ref_invoice_vals = invoice_vals
                    is_service_quotation = invoice_vals.pop('is_service_quotation', False)
                else:
                    ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                origins.add(invoice_vals['invoice_origin'])
                # payment_refs.add(invoice_vals['payment_reference'])
                refs.append(invoice_vals.get('ref', False))
                grn_tracking.append(invoice_vals.get('grn_tracking', False))
                tracking_ref.append(invoice_vals.get('tracking_ref', False))
                invoice_vals.pop('is_service_quotation', None)
            ref_invoice_vals.update({
                'invoice_origin': ', '.join(origins),
                # panworld details
                'po_ref_ids': [(6, 0, self.ids)],
                'grn_tracking': ', '.join(list(set(filter(bool, grn_tracking)))),
                'tracking_ref': ', '.join(list(set(filter(bool, tracking_ref)))),
                'is_service_quotation_bill': is_service_quotation,
            })
            new_invoice_vals_list.append(ref_invoice_vals)
        invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.
        invoices = self.env['account.move']
        AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
        for vals in invoice_vals_list:
            invoices |= AccountMove.with_company(vals['company_id']).create(vals)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        invoices.filtered(lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_move_type()

        # 5) Link the attachments to the invoice
        attachments = self.env['ir.attachment'].browse(attachment_ids)
        if not attachments:
            return self.action_view_invoice(invoices)

        if len(invoices) != 1:
            raise ValidationError(_("You can only upload a bill for a single vendor at a time."))
        invoices.with_context(skip_is_manually_modified=True)._extend_with_attachments(
            invoices._to_files_data(attachments),
            new=True,
        )

        invoices.message_post(attachment_ids=attachments.ids)

        attachments.write({'res_model': 'account.move', 'res_id': invoices.id})
        return self.action_view_invoice(invoices)

    def _prepare_invoice(self):
        """Override method to pass values to create the new invoice for a purchase order.
        """
        res = super()._prepare_invoice()
        picking = self.picking_ids.filtered(
                lambda r: r.picking_type_code == 'incoming' and r.state != 'cancel')
        if len(picking) > 1:
            picking = picking[0]
        res.update({'po_ref_ids': [(4, self.id)],
                    'grn_tracking': picking.carrier_tracking_ref or False,
                    'tracking_ref': self.customer_sales_order,
                    'date': picking.scheduled_date and picking.scheduled_date.date() or fields.Date.today()
                    })
        return res

    def action_export_xls(self, mail_attach=False):
        self.ensure_one()
        return self.env['purchase.xls.wizard'].action_export_xls(self.id, mail_attach)

    def action_rfq_export_xls(self, mail_attach=False):
        self.ensure_one()
        return self.env['purchase.xls.wizard'].action_rfq_export_xls(self.id, mail_attach)

    @api.model
    def _prepare_sale_order_line_data(self, line, company):
        """ Generate the Sales Order Line values from the PO line
            :param line : the origin Purchase Order Line
            :rtype line : purchase.order.line record
            :param company : the company of the created SO
            :rtype company : res.company record
        """
        # it may not affected because of parallel company relation

        res = super()._prepare_sale_order_line_data(line, company)
        price = line.price_unit or 0.0
        price = line.product_id and line.product_uom_id._compute_price(price, line.product_id.uom_id) or price
        so_quantity = line.product_id and line.product_uom_id._compute_quantity(line.po_qty,
                                                                             line.product_id.uom_id) or line.po_qty
        so_qty = line.product_id and line.product_uom_id._compute_quantity(line.rfq_qty,
                                                                        line.product_id.uom_id) or line.rfq_qty

        res.update({'list_price': price or 0.0,
                    'so_quantity': so_quantity,
                    'so_qty': so_qty,
                    })
        return res

    def get_merge_duplicate_lines(self):
        # Get merge duplicate lines for report.
        product_dict_res = {}
        for po_line in self.order_line:
            po_line.ensure_one()
            if po_line.discount:
                price_unit = (po_line.po_price * (1 - po_line.discount / 100))
            else:
                price_unit = po_line.po_price
            po_price_with_disc = price_unit
            if po_line.product_id.id not in product_dict_res:
                product_dict_res[po_line.product_id.id] = {
                    'product_id': po_line.product_id,
                    'product_uom_id': po_line.product_uom_id.name,
                    # 'product_qty': int(po_line.product_qty),
                    'product_qty': int(po_line.rfq_qty),
                    'list_price': po_line.list_price,
                    'discount': po_line.discount,
                    'price_unit': po_line.price_unit,
                    'price_subtotal': po_line.price_subtotal,
                    'tax_ids': (', '.join(map(lambda x: x.name, po_line.tax_ids))),
                    # 'vat_amount': ( po_price_with_disc * sum(po_line.taxes_id.mapped('amount')) ) / 100, #po_line.price_total - po_line.price_subtotal,
                    'vat_amount': float(po_line.price_total - po_line.price_subtotal), #po_line.price_total - po_line.price_subtotal,
                    'price_total': po_line.po_price + (po_price_with_disc * sum(po_line.tax_ids.mapped('amount')) ) / 100 ,#po_line.price_total,
                    "po_qty": po_line.po_qty,
                    "po_list_price": po_line.po_list_price,
                    "po_discount": po_line.po_discount,
                    "po_price": po_line.po_price,
                    "po_subtotal": po_line.po_subtotal

                }
            else:
                # product_dict_res[po_line.product_id.id]['product_qty'] += int(po_line.product_qty)
                product_dict_res[po_line.product_id.id]['product_qty'] += int(po_line.rfq_qty)
                product_dict_res[po_line.product_id.id]['price_subtotal'] += po_line.price_subtotal
                product_dict_res[po_line.product_id.id]['vat_amount'] += po_line.price_total - po_line.price_subtotal
                product_dict_res[po_line.product_id.id]['price_total'] += po_line.price_total
        return product_dict_res

    def _add_supplier_to_product(self):
        """
        Override to use po_list_price (Gross) and allow multiple entries
        for the same vendor if the price differs (Price History).
        """
        for line in self.order_line:
            # Do not add a contact as a supplier
            partner = self.partner_id if not self.partner_id.parent_id else self.partner_id.parent_i
            if not line.product_id:
                continue
            # Determine Price: Use po_list_price (Gross) if available, else fallback
            price = line.po_list_price if line.po_list_price else line.price_unit
            # Compute the price for the template's UoM
            if line.product_id.product_tmpl_id.uom_id != line.product_uom_id:
                default_uom = line.product_id.product_tmpl_id.uom_id
                price = line.product_uom_id._compute_price(price, default_uom)
            # Check for EXISTING matching seller (Partner + Currency + Same Price)
            # Standard Odoo only checks 'partner', we add 'price' to the check
            currency = line.currency_id
            existing_sellers = line.product_id.seller_ids.filtered(lambda s:
                                                                   s.partner_id == partner and
                                                                   s.currency_id == currency and
                                                                   abs(s.price - price) < 0.01  # Float comparison
                                                                   )
            # If no exact price match found, add a new one
            if not existing_sellers:
                supplierinfo = self._prepare_supplier_info(partner, line, price, currency)
                # In case the order partner is a contact address (e.g. branch)
                # we keep the product name and code
                seller = line.product_id._select_seller(
                    partner_id=line.partner_id,
                    quantity=line.product_qty,
                    date=line.order_id.date_order and line.order_id.date_order.date(),
                    uom_id=line.product_uom_id)
                if seller:
                    supplierinfo['product_name'] = seller.product_name
                    supplierinfo['product_code'] = seller.product_code
                vals = {
                    'seller_ids': [(0, 0, supplierinfo)],
                }
                line.product_id.product_tmpl_id.sudo().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        orders = super(PurchaseOrder, self).create(vals_list)
        for order in orders:
            if order.state in ['draft', 'sent', 'to approve', 'cancel']:
                 order.presale_original_name = order.name
                 # Swap Prefix: P -> RFQ
                 if order.name.startswith('P'):
                     order.name = 'RFQ' + order.name[1:]
        return orders
