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
from odoo.osv import expression


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    shipping_option_id = fields.Many2one(
        "purchase.shipping.options.rule",
        "Shipping Options",
        domain="[('company_id', '=', current_company_id)]",
        default=lambda self: self.env["purchase.shipping.options.rule"].search(
            [("default_option", "=", True)], limit=1
        ),
        help="Select Shipping options Direct ship or via shipper",
    )
    carrier_type = fields.Selection(
        [("sale", "Sale"), ("purchase", "Purchase")],
        string="Applicable For",
        default="sale",
    )
    additional_service_ids = fields.One2many(
        "additional.delivery.carrier.lines", "carrier_id", "Additional Services"
    )
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street2')
    city = fields.Char(string='City')
    zip = fields.Char(string='Zip')
    state_id = fields.Many2one(
        'res.country.state', string="State", domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string="Country")
    street1 = fields.Char(string='Street1')
    telephone = fields.Char(string='Telephone')
    target_weight = fields.Float(string='TargetWeight')

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, **kwargs):
        args = args or []
        context = self.env.context or {}
        domain = []

        if context.get("from_purchase_order") and context.get("partner_id"):
            vendor = self.env["res.partner"].browse(context.get("partner_id"))
            vendor_country = vendor.country_id

            domain = [
                ("carrier_type", "=", "purchase"),
                ("company_id", "=", self.env.company.id),
                "|",
                ("country_ids", "in", vendor_country.ids),
                ("country_ids", "=", False),
            ]

        elif context.get("from_stock_picking") and context.get("partner_id"):
            partner = self.env["res.partner"].browse(context.get("partner_id"))
            domain = [
                "|",
                ("country_ids", "in", partner.country_id.ids),
                ("country_ids", "=", False),
            ]

        if domain:
            args = fields.Domain.AND([args, domain])

        return super(DeliveryCarrier, self)._search(args, offset, limit, order, **kwargs)