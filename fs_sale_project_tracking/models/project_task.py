# -*- coding: utf-8 -*-

import base64
import csv
import io
from datetime import datetime
from odoo import api, fields, models, _


class ProjectTask(models.Model):
    _inherit = 'project.task'

    fs_sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        help="The sale order being tracked by this task")
    
    # Sale Order Tracking Fields
    sale_order_state = fields.Selection(
        related='fs_sale_order_id.state',
        string='SO Status')
    
    sale_order_amount = fields.Monetary(
        related='fs_sale_order_id.amount_total',
        string='SO Amount')
    
    currency_id = fields.Many2one(
        related='fs_sale_order_id.currency_id',
        string='Currency')
    
    # Delivery Tracking
    delivery_count = fields.Integer(
        string='Deliveries',
        compute='_compute_delivery_info')
    
    delivery_status = fields.Char(
        string='Delivery Status',
        compute='_compute_delivery_info')
    
    # Purchase Requisition Tracking
    requisition_count = fields.Integer(
        string='Requisitions',
        compute='_compute_requisition_info')
    
    requisition_status = fields.Char(
        string='Requisition Status',
        compute='_compute_requisition_info')
    
    # Purchase Order Tracking
    purchase_order_count = fields.Integer(
        string='Purchase Orders',
        compute='_compute_purchase_order_info')
    
    purchase_order_status = fields.Char(
        string='PO Status',
        compute='_compute_purchase_order_info')
    
    # Quantity Tracking Fields
    total_qty_ordered = fields.Float(
        string='Total Qty Ordered',
        compute='_compute_qty_totals',
        digits='Product Unit of Measure')
    
    total_qty_delivered = fields.Float(
        string='Total Qty Delivered',
        compute='_compute_qty_totals',
        digits='Product Unit of Measure')
    
    total_qty_pending = fields.Float(
        string='Total Qty Pending',
        compute='_compute_qty_totals',
        digits='Product Unit of Measure')

    # Purchase Quantity Tracking Fields
    total_qty_purchased = fields.Float(
        string='Total Qty Purchased',
        compute='_compute_purchase_qty_totals',
        digits='Product Unit of Measure',
        help="Total quantity in confirmed purchase orders")
    
    total_qty_received = fields.Float(
        string='Total Qty Received',
        compute='_compute_purchase_qty_totals',
        digits='Product Unit of Measure',
        help="Total quantity received from purchase orders")
    
    total_qty_pending_purchase = fields.Float(
        string='Qty Pending Purchase',
        compute='_compute_purchase_qty_totals',
        digits='Product Unit of Measure',
        help="Quantity yet to be received from purchase orders")

    @api.depends('fs_sale_order_id', 'fs_sale_order_id.order_line', 
                 'fs_sale_order_id.order_line.product_uom_qty',
                 'fs_sale_order_id.order_line.qty_delivered')
    def _compute_qty_totals(self):
        """Compute total quantities from sale order lines"""
        for task in self:
            if task.fs_sale_order_id and task.fs_sale_order_id.order_line:
                lines = task.fs_sale_order_id.order_line.filtered(
                    lambda l: l.product_id.type in ['product', 'consu'])
                task.total_qty_ordered = sum(lines.mapped('product_uom_qty'))
                task.total_qty_delivered = sum(lines.mapped('qty_delivered'))
                task.total_qty_pending = task.total_qty_ordered - task.total_qty_delivered
            else:
                task.total_qty_ordered = 0
                task.total_qty_delivered = 0
                task.total_qty_pending = 0

    @api.depends('fs_sale_order_id')
    def _compute_delivery_info(self):
        """Compute delivery information"""
        for task in self:
            if task.fs_sale_order_id and hasattr(task.fs_sale_order_id, 'picking_ids'):
                pickings = task.fs_sale_order_id.picking_ids.filtered(
                    lambda p: p.picking_type_code == 'outgoing')
                task.delivery_count = len(pickings)
                
                if pickings:
                    states = pickings.mapped('state')
                    if all(s == 'done' for s in states):
                        task.delivery_status = 'Done'
                    elif any(s == 'done' for s in states):
                        task.delivery_status = f'Partial ({len([s for s in states if s == "done"])}/{len(states)})'
                    elif any(s == 'assigned' for s in states):
                        task.delivery_status = 'Ready'
                    else:
                        task.delivery_status = 'Waiting'
                else:
                    task.delivery_status = 'No Delivery'
            else:
                task.delivery_count = 0
                task.delivery_status = '-'

    @api.depends('fs_sale_order_id')
    def _compute_requisition_info(self):
        """Compute purchase requisition information"""
        for task in self:
            if task.fs_sale_order_id:
                requisitions = self.env['material.purchase.requisition'].search([
                    ('fs_sale_order_id', '=', task.fs_sale_order_id.id)
                ])
                task.requisition_count = len(requisitions)
                
                if requisitions:
                    states = requisitions.mapped('state')
                    if all(s == 'done' for s in states):
                        task.requisition_status = 'Done'
                    elif all(s == 'stock' for s in states):
                        task.requisition_status = 'PO Created'
                    elif all(s == 'approved' for s in states):
                        task.requisition_status = 'Approved'
                    elif any(s == 'reject' for s in states):
                        task.requisition_status = 'Rejected'
                    elif any(s in ('approved', 'stock', 'done') for s in states):
                        approved_count = len([s for s in states if s in ('approved', 'stock', 'done')])
                        task.requisition_status = f'In Progress ({approved_count}/{len(states)})'
                    elif all(s == 'pending' for s in states):
                        task.requisition_status = 'Pending'
                    else:
                        task.requisition_status = 'Draft'
                else:
                    task.requisition_status = 'Not Created'
            else:
                task.requisition_count = 0
                task.requisition_status = '-'

    @api.depends('fs_sale_order_id')
    def _compute_purchase_order_info(self):
        """Compute purchase order information from direct link and requisitions"""
        for task in self:
            if task.fs_sale_order_id:
                # Get POs directly linked to the sale order
                direct_pos = self.env['purchase.order'].search([
                    ('fs_sale_order_id', '=', task.fs_sale_order_id.id)
                ])
                
                # Also get POs from requisitions for backward compatibility
                requisitions = self.env['material.purchase.requisition'].search([
                    ('fs_sale_order_id', '=', task.fs_sale_order_id.id)
                ])
                requisition_pos = requisitions.mapped('purchase_order_ids')
                
                # Combine and deduplicate
                purchase_orders = direct_pos | requisition_pos
                task.purchase_order_count = len(purchase_orders)
                
                if purchase_orders:
                    states = purchase_orders.mapped('state')
                    if all(s == 'purchase' for s in states):
                        task.purchase_order_status = 'Done'
                    elif any(s in ['sent', 'to approve'] for s in states):
                        task.purchase_order_status = f'In Progress ({len([s for s in states if s in ["sent", "to approve"]])}/{len(states)})'
                    else:
                        task.purchase_order_status = 'Draft'
                else:
                    task.purchase_order_status = 'Not Created'
            else:
                task.purchase_order_count = 0
                task.purchase_order_status = '-'

    @api.depends('fs_sale_order_id')
    def _compute_purchase_qty_totals(self):
        """Compute total quantities from purchase orders linked to sale order"""
        for task in self:
            if task.fs_sale_order_id:
                # Get POs directly linked to the sale order
                direct_pos = self.env['purchase.order'].search([
                    ('fs_sale_order_id', '=', task.fs_sale_order_id.id),
                    ('state', 'in', ['purchase', 'done'])
                ])
                
                # Also get POs from requisitions
                requisitions = self.env['material.purchase.requisition'].search([
                    ('fs_sale_order_id', '=', task.fs_sale_order_id.id)
                ])
                requisition_pos = requisitions.mapped('purchase_order_ids').filtered(
                    lambda po: po.state in ['purchase', 'done']
                )
                
                # Combine and deduplicate
                purchase_orders = direct_pos | requisition_pos
                
                if purchase_orders:
                    # Sum quantities from PO lines
                    total_purchased = 0
                    total_received = 0
                    for po in purchase_orders:
                        for line in po.order_line:
                            total_purchased += line.product_qty
                            total_received += line.qty_received
                    
                    task.total_qty_purchased = total_purchased
                    task.total_qty_received = total_received
                    task.total_qty_pending_purchase = total_purchased - total_received
                else:
                    task.total_qty_purchased = 0
                    task.total_qty_received = 0
                    task.total_qty_pending_purchase = 0
            else:
                task.total_qty_purchased = 0
                task.total_qty_received = 0
                task.total_qty_pending_purchase = 0

    def action_create_purchase_requisition(self):
        """Open wizard to create purchase requisition from sale order lines"""
        self.ensure_one()
        
        if not self.fs_sale_order_id:
            from odoo.exceptions import UserError
            raise UserError(_('No sale order linked to this task.'))
        
        if not self.fs_sale_order_id.order_line:
            from odoo.exceptions import UserError
            raise UserError(_('Sale order has no lines to create requisition from.'))
        
        # Create wizard
        wizard = self.env['fs.create.requisition.wizard'].create({
            'task_id': self.id,
            'sale_order_id': self.fs_sale_order_id.id,
        })
        
        # Create wizard lines from sale order lines
        for line in self.fs_sale_order_id.order_line:
            if line.product_id.type in ['product', 'consu']:  # Only stockable and consumable
                self.env['fs.create.requisition.wizard.line'].create({
                    'wizard_id': wizard.id,
                    'sale_line_id': line.id,
                    'product_id': line.product_id.id,
                    'description': line.name,
                    'qty_ordered': line.product_uom_qty,
                    'qty_requisition': line.product_uom_qty,
                    'uom_id': line.product_uom_id.id,
                    'selected': True,
                })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Purchase Requisition'),
            'res_model': 'fs.create.requisition.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_view_sale_order(self):
        """View the linked sale order"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sale Order'),
            'res_model': 'sale.order',
            'res_id': self.fs_sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_deliveries(self):
        """View delivery orders"""
        self.ensure_one()
        pickings = self.fs_sale_order_id.picking_ids.filtered(
            lambda p: p.picking_type_code == 'outgoing')
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Deliveries'),
            'res_model': 'stock.picking',
            'domain': [('id', 'in', pickings.ids)],
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_view_requisitions(self):
        """View purchase requisitions"""
        self.ensure_one()
        requisitions = self.env['material.purchase.requisition'].search([
            ('fs_sale_order_id', '=', self.fs_sale_order_id.id)
        ])
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Requisitions'),
            'res_model': 'material.purchase.requisition',
            'domain': [('id', 'in', requisitions.ids)],
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_view_purchase_orders(self):
        """View purchase orders linked directly or via requisitions"""
        self.ensure_one()
        # Get POs directly linked to the sale order
        direct_pos = self.env['purchase.order'].search([
            ('fs_sale_order_id', '=', self.fs_sale_order_id.id)
        ])
        
        # Also get POs from requisitions
        requisitions = self.env['material.purchase.requisition'].search([
            ('fs_sale_order_id', '=', self.fs_sale_order_id.id)
        ])
        requisition_pos = requisitions.mapped('purchase_order_ids')
        
        # Combine and deduplicate
        purchase_orders = direct_pos | requisition_pos
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Orders'),
            'res_model': 'purchase.order',
            'domain': [('id', 'in', purchase_orders.ids)],
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_download_tracking_status(self):
        """Download tracking status as CSV"""
        self.ensure_one()
        
        if not self.fs_sale_order_id:
            from odoo.exceptions import UserError
            raise UserError(_('No sale order linked to this task.'))
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        so = self.fs_sale_order_id
        
        # Section 1: Header
        writer.writerow(['# TRACKING STATUS REPORT'])
        writer.writerow([f'# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'])
        writer.writerow([f'# Task: {self.name}'])
        writer.writerow([f'# Sale Order: {so.name}'])
        writer.writerow([f'# Customer: {so.partner_id.name}'])
        writer.writerow([f'# SO Status: {dict(so._fields["state"].selection).get(so.state, so.state)}'])
        writer.writerow([f'# SO Total: {so.currency_id.symbol} {so.amount_total:,.2f}'])
        writer.writerow([])
        
        # Section 2: Summary Totals
        writer.writerow(['SUMMARY'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['SO Total', f'{so.currency_id.symbol} {so.amount_total:,.2f}'])
        writer.writerow(['Total Qty Ordered', f'{self.total_qty_ordered:,.2f}'])
        writer.writerow(['Total Qty Delivered', f'{self.total_qty_delivered:,.2f}'])
        writer.writerow(['Total Qty Pending', f'{self.total_qty_pending:,.2f}'])
        
        if self.total_qty_ordered > 0:
            delivery_pct = (self.total_qty_delivered / self.total_qty_ordered) * 100
            writer.writerow(['Delivery Coverage %', f'{delivery_pct:.1f}%'])
        writer.writerow([])
        
        # Section 3: Document Status
        writer.writerow(['DOCUMENT STATUS'])
        writer.writerow(['Document Type', 'Status', 'Count'])
        writer.writerow(['Sale Order', dict(so._fields['state'].selection).get(so.state, so.state), 1])
        writer.writerow(['Deliveries', self.delivery_status, self.delivery_count])
        writer.writerow(['Purchase Requisitions', self.requisition_status, self.requisition_count])
        writer.writerow(['Purchase Orders', self.purchase_order_status, self.purchase_order_count])
        writer.writerow([])
        
        # Section 4: Product Details
        writer.writerow(['PRODUCT DETAILS'])
        writer.writerow([
            'Product Code', 'Product Name', 'Ordered Qty', 'Delivered Qty', 
            'Pending Delivery', 'Delivery %', 'Requisition Qty', 'PO Qty', 
            'Received Qty', 'Pending Purchase', 'Purchase %', 'Vendor(s)',
            'UoM', 'Unit Price', 'Subtotal'
        ])
        
        # Get requisitions and PO data
        requisitions = self.env['material.purchase.requisition'].search([
            ('fs_sale_order_id', '=', so.id)
        ])
        purchase_orders = requisitions.mapped('purchase_order_ids')
        
        # Build product-level data
        for line in so.order_line.filtered(lambda l: l.product_id.type in ['product', 'consu']):
            product = line.product_id
            ordered_qty = line.product_uom_qty
            delivered_qty = line.qty_delivered
            pending_delivery = ordered_qty - delivered_qty
            delivery_pct = (delivered_qty / ordered_qty * 100) if ordered_qty > 0 else 0
            
            # Find requisition qty for this product
            req_qty = 0
            for req in requisitions:
                if hasattr(req, 'requisition_line_ids'):
                    for req_line in req.requisition_line_ids:
                        if req_line.product_id.id == product.id:
                            req_qty += req_line.qty if hasattr(req_line, 'qty') else 0
            
            # Find PO qty and vendors for this product
            po_qty = 0
            received_qty = 0
            vendors = set()
            for po in purchase_orders:
                for po_line in po.order_line:
                    if po_line.product_id.id == product.id:
                        po_qty += po_line.product_qty
                        received_qty += po_line.qty_received
                        vendors.add(po.partner_id.name)
            
            pending_purchase = po_qty - received_qty
            purchase_pct = (received_qty / po_qty * 100) if po_qty > 0 else 0
            vendor_str = ', '.join(vendors) if vendors else '-'
            
            writer.writerow([
                product.default_code or '-',
                product.name,
                f'{ordered_qty:,.2f}',
                f'{delivered_qty:,.2f}',
                f'{pending_delivery:,.2f}',
                f'{delivery_pct:.1f}%',
                f'{req_qty:,.2f}',
                f'{po_qty:,.2f}',
                f'{received_qty:,.2f}',
                f'{pending_purchase:,.2f}',
                f'{purchase_pct:.1f}%',
                vendor_str,
                line.product_uom_id.name,
                f'{line.price_unit:,.2f}',
                f'{line.price_subtotal:,.2f}',
            ])
        
        # Create attachment and return download action
        csv_content = output.getvalue()
        output.close()
        
        filename = f'tracking_status_{so.name.replace("/", "_")}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(csv_content.encode('utf-8')),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'text/csv',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

