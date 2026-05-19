# -*- coding: utf-8 -*-
from odoo import models, fields

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    priority = fields.Selection(selection_add=[
        ('4', 'Urgent'),
        ('5', 'Critical'),
    ], ondelete={'4': 'set default', '5': 'set default'})
