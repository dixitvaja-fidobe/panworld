# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################

from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class WizSalePurchase(models.TransientModel):
    """Wiz Sale Purchase TransientModel ."""

    _name = "wiz.sale.purchase"
    _description = "Wizard Sale Purchase Order"

    vendor_id = fields.Many2one("res.partner", string="Vendor")
    schedule_date = fields.Datetime(string="Scheduled Date", default=datetime.today())
    order_selection = fields.Selection(
        [("rfq", "RFQ"), ("purchase", "Purchase Order")],
        string="Order Selection",
        default="rfq",
    )
    order_lines_ids = fields.One2many("wiz.sale.purchase.line", "wiz_sale_purchase_id")
    vendor_option = fields.Selection(
        [("single", "Single Vendor"), ("multi", "Multi Vendor")], default="single"
    )
    company_id = fields.Many2one(
        "res.company", "Company", default=lambda self: self.env.company.id
    )
    l10n_in_company_country_code = fields.Char(
        related="company_id.country_id.code", string="Country code", store=True
    )
    l10n_in_purchase = fields.Boolean(
        compute="_compute_is_l10n_in_purchase",
        string="Is l10n In Purchase?",
        store=True,
    )
    l10n_in_sale = fields.Boolean(
        compute="_compute_is_l10n_in_sale", string="Is l10n In Sale?", store=True
    )
    l10n_in_gst_treatment = fields.Selection(
        [
            ("regular", "Registered Business - Regular"),
            ("composition", "Registered Business - Composition"),
            ("unregistered", "Unregistered Business"),
            ("consumer", "Consumer"),
            ("overseas", "Overseas"),
            ("special_economic_zone", "Special Economic Zone"),
            ("deemed_export", "Deemed Export"),
        ],
        string="GST Treatment",
    )

    @api.depends("vendor_option", "order_lines_ids", "order_selection", "company_id")
    def _compute_is_l10n_in_sale(self):
        """Method to compute the l10n_in_sale."""
        for wiz in self:
            wiz.l10n_in_sale = (
                self.env["ir.module.module"]
                .sudo()
                .search_count(
                    [("name", "=", "l10n_in_sale"), ("state", "=", "installed")]
                )
            )

    @api.depends("vendor_option", "order_lines_ids", "order_selection", "company_id")
    def _compute_is_l10n_in_purchase(self):
        """Method to compute the l10n_in_purchase."""
        for wiz in self:
            wiz.l10n_in_purchase = (
                self.env["ir.module.module"]
                .sudo()
                .search_count(
                    [("name", "=", "l10n_in_purchase"), ("state", "=", "installed")]
                )
            )

    def _get_order_lines(self, order_lines=None):
        """Get Order lines to create PO."""
        if order_lines is None:
            order_lines = []
        po_l_vals = []
        if order_lines:
            po_l_vals = [
                (
                    0,
                    0,
                    {
                        "product_id": line.product_id.id,
                        "name": line.product_id.display_name,
                        "product_qty": line.qty,
                        "list_price": line.price_unit,
                        "price_unit": line.price_unit,
                        "product_uom_id": line.uom_id.id,
                        "taxes_id": line.taxes_id and [(6, 0, line.taxes_id.ids)] or [],
                        "sale_line_id": line.sale_line_id.id,
                        "sale_reference": line.sale_reference
                    },
                )
                for line in order_lines
            ]
        return po_l_vals

    def action_create_purchase_order(self):
        """Button method to create purchase order."""
        purchase_obj = self.env["purchase.order"]
        sale_rec = self.env[self.env.context["active_model"]].browse(
            self.env.context["active_ids"]
        )
        vals = {
            "name": "New",
            # "origin": ' ,'.join(sale_rec.mapped('name')) or "",
        }
        for wiz in self:
            if not wiz.order_lines_ids:
                raise ValidationError(
                    _(
                        "Without order lines you "
                        "cannot create purchase order."
                        "\nPlease select at least "
                        "one order line."
                    )
                )
            is_purchase_flag = False
            if wiz.order_selection == "purchase":
                is_purchase_flag = True
                vals.update({"date_approve": wiz.schedule_date})
            else:
                vals.update({"date_order": wiz.schedule_date})

            if wiz.vendor_option == "single":
                if wiz.l10n_in_purchase:
                    vals.update({"l10n_in_gst_treatment": wiz.l10n_in_gst_treatment})
                vals.update(
                    {
                        "partner_id": wiz.vendor_id.id,
                        "order_line": self._get_order_lines(wiz.order_lines_ids),
                    }
                )
                purchase_obj |= purchase_obj.create(vals)
            else:
                vendors = wiz.order_lines_ids.mapped("vendor_id")
                vendor_check = wiz.order_lines_ids.filtered(
                    lambda vendor: not vendor.vendor_id
                )
                if vendor_check:
                    raise ValidationError(
                        _(
                            "Without vendor selection you "
                            "cannot create purchase order."
                            "\n Please select vendor "
                            "in order line."
                        )
                    )
                if not vendors:
                    raise ValidationError(
                        _(
                            "Without vendor selection you "
                            "cannot create purchase order."
                            "\n Please select vendor "
                            "at least in one order line."
                        )
                    )
                for vendor in vendors:
                    vendor_line = wiz.order_lines_ids.filtered(
                        lambda v: v.vendor_id == vendor
                    )
                    if wiz.l10n_in_purchase:
                        gst_treats = list(
                            set(vendor_line.mapped("l10n_in_gst_treatment"))
                        )
                        for gst_treat in gst_treats:
                            gst_v_lines = vendor_line.filtered(
                                lambda v: v.l10n_in_gst_treatment == gst_treat
                            )
                            vals.update(
                                {
                                    "l10n_in_gst_treatment": gst_treat,
                                    "name": "New",
                                    "partner_id": vendor.id,
                                    "order_line": self._get_order_lines(gst_v_lines),
                                }
                            )
                            purchase_obj |= purchase_obj.create(vals)
                    else:
                        vals.update(
                            {
                                "name": "New",
                                "partner_id": vendor.id,
                                "order_line": self._get_order_lines(vendor_line),
                            }
                        )
                        purchase_obj |= purchase_obj.create(vals)
            if purchase_obj:
                if is_purchase_flag:
                    purchase_obj.button_confirm()

    @api.model
    def default_get(self, fields):
        """Default_get method.

        For getting the order lines from sales order
        in create purchase order wizard.
        """
        context = self.env.context
        sale_vals = []
        res = super(WizSalePurchase, self).default_get(fields)
        company = self.env.company
        country_code = company.country_id.code
        # Added active_ids to get result from tree view
        sale_order = self.env["sale.order"].browse(context.get("active_ids"))
        if sale_order and sale_order[0].company_id:
            res.update(
                {
                    "company_id": sale_order[0]
                    and sale_order[0].company_id
                    and sale_order[0].company_id.id
                }
            )
        for order in sale_order:
            vals = [
                    (
                        0,
                        0,
                        {
                            "name": order_line.name,
                            "product_id": order_line.product_id.id,
                            "qty": order_line.product_uom_qty,
                            "price_unit": order_line.product_id.standard_price
                            or order_line.price_unit,
                            "uom_id": order_line.product_uom_id.id,
                            "subtotal": order_line.product_uom_qty
                            * (
                                order_line.product_id.standard_price
                                or order_line.price_unit
                            ),
                            "taxes_id": order_line.product_id
                            and [
                                (
                                    6,
                                    0,
                                    order_line.product_id.supplier_taxes_id
                                    and order_line.product_id.supplier_taxes_id.ids
                                    or [],
                                )
                            ],
                            "sale_line_id": order_line.id,
                            "sale_reference": order_line.order_id.name
                        },
                    )
                    for order_line in order.order_line.filtered(
                        lambda ol: ol.product_id.purchase_ok
                    )
                    if not order_line.display_type
                ]
            sale_vals.extend(vals)

            l10n_in_sale = (
                self.env["ir.module.module"]
                .sudo()
                .search_count([("name", "=", "l10n_in_sale"), ("state", "=", "installed")])
            )
            if l10n_in_sale and country_code == "IN":
                res["l10n_in_gst_treatment"] = order.l10n_in_gst_treatment

        res.update(
            {
                "order_lines_ids":sale_vals
            }
        )

        return res

    @api.onchange("vendor_id")
    def onchange_vendor(self):
        for wiz_vendor in self.order_lines_ids:
            if wiz_vendor.wiz_sale_purchase_id.vendor_option == "single":
                if wiz_vendor.wiz_sale_purchase_id.vendor_id:
                    vendor_price = wiz_vendor.product_id.seller_ids.filtered(
                        lambda v: v.partner_id.name == wiz_vendor.wiz_sale_purchase_id.vendor_id
                    ).mapped("price")
                    wiz_vendor.price_unit = (
                        min(vendor_price)
                        if vendor_price
                        else wiz_vendor.product_id.standard_price or 1.0
                    )
            if wiz_vendor.wiz_sale_purchase_id.vendor_option == "multi":
                wiz_vendor.wiz_sale_purchase_id.vendor_id = False

    @api.onchange("product_id", "vendor_option")
    def onchange_vendor_id(self):
        """This is onchange use to set the product price unit"""
        if self.vendor_option == "multi":
            for line in self.order_lines_ids:
                if line.product_id.seller_ids:
                    line.vendor_id = line.product_id.seller_ids[0].partner_id.name or False
                    line.price_unit = line.product_id.seller_ids[0].price or 0

        if self.vendor_option == "single":
            for line in self.order_lines_ids:
                line.price_unit = line.product_id.standard_price or line.price_unit


