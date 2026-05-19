# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
from odoo import api, models


class ResPartner(models.Model):
    """Model res partner extended."""
    _inherit = "res.partner"

    @api.model
    def name_search(self, name="", domain=None, operator="ilike", limit=100):
        """Overwritten this method for the select only product vendor in the wizard."""
        context = self.env.context or {}
        domain = domain or []
        vendor_ids = []
        if context.get("product_id"):
            product_id = self.env["product.product"].search(
                [("id", "=", context.get("product_id"))], limit=1
            )
            if product_id.seller_ids:
                for vendor_id in product_id.seller_ids:
                    vendor_ids.append(vendor_id.name.id)
                domain = [("id", "in", vendor_ids)]
        return super().name_search(name, domain, operator, limit=limit)
