# -*- coding: utf-8 -*-
from odoo import models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _load_pos_data_domain(self, data, config):
        domain = super()._load_pos_data_domain(data, config)
        if config.default_customer_id:
            if domain and domain[0][0] == 'id' and domain[0][1] == 'in':
                partner_ids = set(domain[0][2])
                partner_ids.add(config.default_customer_id.id)
                domain = [('id', 'in', list(partner_ids))]
            else:
                domain = ['|', ('id', '=', config.default_customer_id.id)] + domain
        return domain
