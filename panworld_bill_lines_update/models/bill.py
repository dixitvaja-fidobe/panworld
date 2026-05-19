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


class AccountTus(models.Model):
    _inherit = 'account.move'


    def bill_lines_update(self):
        view_id = self.env.ref("panworld_import.import_bill_invoice_data_wizard_view")
        return {
            "name": "Update Lines",
            "view_mode": "form",
            "res_model": "import.data.wizard",
            "view_type": "form",
            "view_id": view_id.id,
            "type": "ir.actions.act_window",
            "target": "new",
        }

    def action_update_po_price(self):
        for move in self:
            if move.move_type != 'in_invoice':
                continue
            updated_count = 0
            for line in move.invoice_line_ids:
                if line.purchase_line_id:
                    old_price = line.purchase_line_id.price_unit
                    line.purchase_line_id.write({
                        'price_unit': line.price_unit
                    })
                    line.purchase_line_id.order_id.message_post(
                        body=_("Unit price updated from Vendor Bill %s for product %s: %s -> %s") % (
                            move.name, line.product_id.display_name, old_price, line.price_unit)
                    )
                    updated_count += 1

            if updated_count > 0:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Successfully updated %s Purchase Order lines.') % updated_count,
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Warning'),
                        'message': _('No Purchase Order lines found to update.'),
                        'type': 'warning',
                        'sticky': False,
                    }
                }
