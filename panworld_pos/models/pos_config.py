# -*- coding: utf-8 -*-

from odoo import fields, models, api

class PosConfig(models.Model):
    _inherit = 'pos.config'

    default_customer_id = fields.Many2one(
        'res.partner',
        string='Default Customer',
        help="Customer automatically assigned to a POS order when the 'Can invoice' option is enabled."
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'default_customer_id' not in vals:
                vals['default_customer_id'] = self.env['ir.default']._get('pos.config', 'default_customer_id')
        return super().create(vals_list)

