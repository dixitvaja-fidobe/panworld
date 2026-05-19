# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class FSCreateRequisitionWizard(models.TransientModel):
    _name = 'fs.create.requisition.wizard'
    _description = 'Create Purchase Requisition from Sale Order'

    task_id = fields.Many2one(
        'project.task',
        string='Task',
        required=True,
        readonly=True)
    
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        required=True,
        readonly=True)
    
    line_ids = fields.One2many(
        'fs.create.requisition.wizard.line',
        'wizard_id',
        string='Order Lines')
    
    requisition_date = fields.Date(
        string='Requisition Date',
        default=fields.Date.today,
        required=True)
    
    notes = fields.Text(string='Notes')

    def action_create_requisition(self):
        """Create purchase requisition from selected lines"""
        self.ensure_one()
        
        # Get selected lines
        selected_lines = self.line_ids.filtered(lambda l: l.selected and l.qty_requisition > 0)
        
        if not selected_lines:
            raise UserError(_('Please select at least one line with quantity greater than 0.'))
        
        # Create purchase requisition
        requisition_vals = {
            'request_date': self.requisition_date,
            'employee_id': self.env.user.employee_id.id or False,
            'fs_sale_order_id': self.sale_order_id.id,
            'fs_task_id': self.task_id.id,
            'reason': f"Created from SO: {self.sale_order_id.name}\n{self.notes or ''}",
        }
        
        requisition = self.env['material.purchase.requisition'].create(requisition_vals)
        
        # Create requisition lines
        for line in selected_lines:
            self.env['material.purchase.requisition.line'].create({
                'requisition_id': requisition.id,
                'product_id': line.product_id.id,
                'description': line.description,
                'qty': line.qty_requisition,
                'uom': line.uom_id.id,
            })
        
        # Post message on task
        self.task_id.message_post(
            body=_('Purchase Requisition created: <a href="#" data-oe-model="material.purchase.requisition" data-oe-id="%s">%s</a>') % (
                requisition.id, requisition.name),
            subject=_('Purchase Requisition Created')
        )
        
        # Return action to open the created requisition
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Requisition'),
            'res_model': 'material.purchase.requisition',
            'res_id': requisition.id,
            'view_mode': 'form',
            'target': 'current',
        }


class FSCreateRequisitionWizardLine(models.TransientModel):
    _name = 'fs.create.requisition.wizard.line'
    _description = 'Purchase Requisition Wizard Line'

    wizard_id = fields.Many2one(
        'fs.create.requisition.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade')
    
    sale_line_id = fields.Many2one(
        'sale.order.line',
        string='Sale Order Line',
        readonly=True)
    
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        readonly=True)
    
    description = fields.Text(
        string='Description',
        readonly=True)
    
    qty_ordered = fields.Float(
        string='Ordered Qty',
        readonly=True,
        help="Original quantity from sale order")
    
    qty_requisition = fields.Float(
        string='Requisition Qty',
        required=True,
        help="Quantity to include in purchase requisition")
    
    uom_id = fields.Many2one(
        'uom.uom',
        string='UoM',
        readonly=True)
    
    selected = fields.Boolean(
        string='Include',
        default=True,
        help="Check to include this line in the requisition")

    @api.onchange('selected')
    def _onchange_selected(self):
        """Reset quantity when deselected"""
        if not self.selected:
            self.qty_requisition = 0

