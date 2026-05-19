# -*- coding: utf-8 -*-

from odoo import fields, models


class MaterialPurchaseRequisition(models.Model):
    _inherit = 'material.purchase.requisition'

    fs_sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        readonly=True,
        help="The sale order from which this requisition was created")
    
    fs_task_id = fields.Many2one(
        'project.task',
        string='Tracking Task',
        readonly=True,
        help="The task from which this requisition was created")

    def _prepare_po_vals(self, rec, partner):
        """Override to include fs_sale_order_id in purchase order"""
        vals = super()._prepare_po_vals(rec, partner)
        if rec.fs_sale_order_id:
            vals['fs_sale_order_id'] = rec.fs_sale_order_id.id
        return vals

