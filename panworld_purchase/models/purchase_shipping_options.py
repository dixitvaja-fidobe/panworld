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


class PurchaseShippingOptionsRule(models.Model):
    _name = "purchase.shipping.options.rule"
    _description = "Purchase Shipping Options Rule"

    name = fields.Char("Name", required=True)
    default_option = fields.Boolean("Set as Default")
    picking_type_id = fields.Many2one(
        "stock.picking.type",
        "Operations Type",
        ondelete="restrict",
        required=True,
        copy=False,
    )
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    is_grn_tracking = fields.Boolean(
        "Tracking(AWB)", help='Set Tracking(AWB) in stock picking in Shipping Options are Direct')
    is_via_shipper = fields.Boolean(string="Via Shipper")

    # Commented due to Not compatible with multi warehouse case
    @api.constrains('is_via_shipper', 'picking_type_id')
    def _check_is_via_shipper(self):
        # Set validation on multiple record with via shipper
        for rec in self:
            multi_via_shipper_rule_rec = self.search([
                ('id', '!=', rec.id),
                ('is_via_shipper', '=', True),
                ('company_id', '=', rec.company_id.id),
            ], limit=1)
            if multi_via_shipper_rule_rec.picking_type_id.warehouse_id == rec.picking_type_id.warehouse_id:
                raise ValidationError(
                    _("Sorry, You are not allowed to create multiple record with via shipper!"))
