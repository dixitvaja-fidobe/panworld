# -*- coding: utf-8 -*-
from odoo import models, fields

class ProjectTask(models.Model):
    _inherit = 'project.task'

    priority = fields.Selection(selection_add=[
        ('4', 'Urgent'),
        ('5', 'Critical'),
    ], ondelete={'4': 'set default', '5': 'set default'})
