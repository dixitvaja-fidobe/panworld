# -*- coding: utf-8 -*-

from markupsafe import Markup
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    tracking_project_id = fields.Many2one(
        'project.project',
        string='Tracking Project',
        default=lambda self: self.env["project.project"].search(
            [("sale_tracking", "=", True)], limit=1, order='create_date'
        ),
        domain=[('sale_tracking', '=', True)],
        tracking=True,
        required=True,
        help="Select a tracking project. A task will be created in this project when order is confirmed.")
    
    tracking_task_id = fields.Many2one(
        'project.task',
        string='Tracking Task',
        readonly=True,
        copy=False,
        help="The task created for tracking this sale order")

    def action_confirm(self):
        """Override to create tracking task"""
        res = super(SaleOrder, self).action_confirm()
        
        for order in self:
            # Create tracking task if project is selected and task not already created
            if order.tracking_project_id and not order.tracking_task_id:
                task_vals = {
                    'name': f"SO Tracking: {order.name}",
                    'project_id': order.tracking_project_id.id,
                    'fs_sale_order_id': order.id,
                    'partner_id': order.partner_id.id,
                    'company_id': order.company_id.id,
                    'description': f"""
                        <p><strong>Sale Order Tracking Task</strong></p>
                        <p>Order: {order.name}</p>
                        <p>Customer: {order.partner_id.name}</p>
                        <p>Total Amount: {order.amount_total} {order.currency_id.name}</p>
                        <p>Order Date: {order.date_order}</p>
                    """,
                }
                task = self.env['project.task'].create(task_vals)
                order.tracking_task_id = task.id
                
                # Post message on sale order
                order.message_post(
                    body=Markup(_('Tracking task created: <a href="#" data-oe-model="project.task" data-oe-id="%s">%s</a>')) % (
                        task.id, task.name),
                    subtype_xmlid='mail.mt_note'
                )
        
        return res

    def action_view_tracking_task(self):
        """Open the tracking task"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tracking Task'),
            'res_model': 'project.task',
            'res_id': self.tracking_task_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

