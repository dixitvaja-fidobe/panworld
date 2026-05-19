# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_default_customer_id = fields.Many2one(
        related='pos_config_id.default_customer_id',
        readonly=False,
        string="Default Customer (POS)",
        help="Customer automatically assigned to a POS order when the 'Can invoice' option is enabled.",
    )

    def set_values(self):
        super().set_values()
        # Propagate the selected customer to all POS configurations and set as default for future ones
        if self.pos_default_customer_id:
            self.env['ir.default'].sudo().set('pos.config', 'default_customer_id', self.pos_default_customer_id.id)
            # Sync existing records safely (avoiding singleton errors in overrides)
            for config in self.env['pos.config'].sudo().search([('id', '!=', self.pos_config_id.id)]):
                config.write({'default_customer_id': self.pos_default_customer_id.id})
