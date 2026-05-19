# -*- coding: utf-8 -*-

from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    sale_tracking = fields.Boolean(
        string='Sale Order Tracking',
        tracking=True,
        help="Enable this to use this project for tracking sale orders")
    
    tracking_task_count = fields.Integer(
        string='Tracking Tasks',
        compute='_compute_tracking_task_count')

    def _compute_tracking_task_count(self):
        """Count tasks with sale orders"""
        for project in self:
            project.tracking_task_count = self.env['project.task'].search_count([
                ('project_id', '=', project.id),
                ('fs_sale_order_id', '!=', False)
            ])

