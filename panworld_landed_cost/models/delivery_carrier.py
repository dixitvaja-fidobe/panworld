# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Fidobe Solutions LLC.
#
#    For Module Support : dev3@fidobe.com
#
#############################################################################
import re

from odoo import SUPERUSER_ID, Command, _, api, fields, models
from odoo.exceptions import UserError, ValidationError

class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def available_carriers(self, partner, source):
        return self.filtered(lambda c: c._match(partner, source))

    def _match(self, partner, source):
        self.ensure_one()
        return (
                self._match_address(partner)
                and self._match_must_have_tags(source)
                and self._match_excluded_tags(source)
                and self._match_weight(source)
                and self._match_volume(source)
        )

    def _match_address(self, partner):
        self.ensure_one()
        if self.country_ids and partner.country_id not in self.country_ids:
            return False
        if self.state_ids and partner.state_id not in self.state_ids:
            return False
        if self.zip_prefix_ids:
            regex = re.compile('|'.join(['^' + zip_prefix for zip_prefix in self.zip_prefix_ids.mapped('name')]))
            if not partner.zip or not re.match(regex, partner.zip.upper()):
                return False
        return True

    def _match_must_have_tags(self, source):
        self.ensure_one()
        if source._name == 'sale.order':
            products = source.order_line.product_id
        elif source._name == 'stock.picking':
            products = source.move_ids.product_id
        elif source._name == 'purchase.order':
            products = source.order_line.product_id
        else:
            raise UserError(_("Invalid source document type"))
        return not self.must_have_tag_ids or any(
            tag in products.all_product_tag_ids
            for tag in self.must_have_tag_ids
        )

    def _match_excluded_tags(self, source):
        self.ensure_one()
        if source._name == 'sale.order':
            products = source.order_line.product_id
        elif source._name == 'stock.picking':
            products = source.move_ids.product_id
        elif source._name == 'purchase.order':
            products = source.order_line.product_id
        else:
            raise UserError(_("Invalid source document type"))
        return not any(tag in products.all_product_tag_ids for tag in self.excluded_tag_ids)

    def _match_weight(self, source):
        self.ensure_one()
        if source._name == 'sale.order':
            total_weight = sum(line.product_id.weight * line.product_qty for line in source.order_line)
        elif source._name == 'stock.picking':
            total_weight = sum(move.product_id.weight * move.product_uom_qty for move in source.move_ids)
        elif source._name == 'purchase.order':
            total_weight = sum(line.product_id.weight * line.product_qty for line in source.order_line)
        else:
            raise UserError(_("Invalid source document type"))
        return not self.max_weight or total_weight <= self.max_weight

    def _match_volume(self, source):
        self.ensure_one()
        if source._name == 'sale.order':
            total_volume = sum(line.product_id.volume * line.product_qty for line in source.order_line)
        elif source._name == 'stock.picking':
            total_volume = sum(move.product_id.volume * move.product_uom_qty for move in source.move_ids)
        elif source._name == 'purchase.order':
            total_volume = sum(line.product_id.volume * line.product_qty for line in source.order_line)
        else:
            raise UserError(_("Invalid source document type"))
        return not self.max_volume or total_volume <= self.max_volume