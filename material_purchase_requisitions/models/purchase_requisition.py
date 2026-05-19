# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import UserError
from markupsafe import Markup


class MaterialPurchaseRequisition(models.Model):
    _name = 'material.purchase.requisition'
    _description = 'Purchase Requisition'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'id desc'

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel', 'reject'):
                raise UserError(
                    _('You can not delete Purchase Requisition which is not in draft or cancelled or rejected state.'))
        return super(MaterialPurchaseRequisition, self).unlink()

    name = fields.Char(
        string='Number',
        index=True,
        readonly=1,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('stock', 'Purchase Order Created'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('reject', 'Rejected')],
        default='draft',
        tracking=True
    )
    request_date = fields.Date(
        string='Requisition Date',
        default=fields.Date.today(),
        required=True,
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        related="employee_id.department_id",
        copy=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1),
        required=True,
        copy=True,
    )
    
    # Approval Fields
    approver_id = fields.Many2one(
        'hr.employee',
        string='Approved By',
        readonly=True,
        copy=False,
    )
    approval_date = fields.Date(
        string='Approval Date',
        readonly=True,
        copy=False,
    )
    reject_employee_id = fields.Many2one(
        'hr.employee',
        string='Rejected By',
        readonly=True,
        copy=False,
    )
    reject_date = fields.Date(
        string='Rejected Date',
        readonly=True,
        copy=False,
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.user.company_id,
        required=True,
        copy=True,
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Source Location',
        copy=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )
    requisition_line_ids = fields.One2many(
        'material.purchase.requisition.line',
        'requisition_id',
        string='Purchase Requisitions Line',
        copy=True,
    )
    date_end = fields.Date(
        string='Requisition Deadline',
        help='Last date for the product to be needed',
        copy=True,
    )
    date_done = fields.Date(
        string='Date Done',
        readonly=True,
        help='Date of Completion of Purchase Requisition',
    )
    reason = fields.Text(
        string='Reason for Requisition',
        copy=True,
    )
    approval_notes = fields.Text(
        string='Approval Notes',
        tracking=True,
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        copy=True,
    )
    requisiton_responsible_id = fields.Many2one(
        'hr.employee',
        string='Requisition Responsible',
        copy=True,
    )
    employee_confirm_id = fields.Many2one(
        'hr.employee',
        string='Confirmed By',
        readonly=True,
        copy=False,
    )
    confirm_date = fields.Date(
        string='Confirmed Date',
        readonly=True,
        copy=False,
    )

    purchase_order_ids = fields.One2many(
        'purchase.order',
        'custom_requisition_id',
        string='Purchase Orders',
    )

    @api.model
    def create(self, vals_list):
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get('name'):
                name = self.env['ir.sequence'].next_by_code('purchase.requisition.seq')
                vals['name'] = name

        res = super(MaterialPurchaseRequisition, self).create(vals_list)
        return res

    def requisition_confirm(self):
        """Confirm requisition and submit for approval"""
        for rec in self:
            manager_mail_template = self.env.ref(
                'material_purchase_requisitions.email_confirm_material_purchase_requistion', raise_if_not_found=False)
            rec.employee_confirm_id = rec.employee_id.id
            rec.confirm_date = fields.Date.today()
            rec.state = 'pending'
            if rec.reason:
                rec.message_post(
                    body=Markup("Requisition submitted for approval by %s<br/>Reason: %s") % (
                        self.env.user.name, rec.reason),
                    message_type="comment",
                    subtype_xmlid="mail.mt_note",
                )
            if manager_mail_template:
                manager_mail_template.send_mail(self.id)

    def requisition_approve(self):
        """Approve the requisition"""
        for rec in self:
            rec.approval_date = fields.Date.today()
            rec.approver_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            rec.state = 'approved'
            if rec.approval_notes:
                rec.message_post(
                    body=Markup("Requisition approved by %s<br/>Notes: %s") % (
                        self.env.user.name, rec.approval_notes),
                    message_type="comment",
                    subtype_xmlid="mail.mt_note",
                )
            else:
                rec.message_post(
                    body=Markup("Requisition approved by %s") % self.env.user.name,
                    message_type="comment",
                    subtype_xmlid="mail.mt_note",
                )
            # Send notification
            mail_template = self.env.ref(
                'material_purchase_requisitions.email_purchase_requisition', raise_if_not_found=False)
            if mail_template:
                mail_template.sudo().send_mail(self.id)

    def requisition_reject(self):
        """Reject the requisition"""
        for rec in self:
            rec.state = 'reject'
            rec.reject_employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            rec.reject_date = fields.Date.today()
            rec.message_post(
                body=Markup("Requisition rejected by %s") % self.env.user.name,
                message_type="comment",
                subtype_xmlid="mail.mt_note",
            )

    def reset_draft(self):
        """Reset to draft state"""
        for rec in self:
            rec.state = 'draft'
            rec.approver_id = False
            rec.approval_date = False
            rec.employee_confirm_id = False
            rec.confirm_date = False
            rec.reject_employee_id = False
            rec.reject_date = False

    @api.model
    def _prepare_po_line(self, line=False, purchase_order=False):
        po_line_vals = {
            'product_id': line.product_id.id,
            'name': line.product_id.name,
            'product_qty': line.qty,
            'product_uom_id': line.uom.id,
            'date_planned': fields.Date.today(),
            'price_unit': line.product_id.standard_price,
            'order_id': purchase_order.id,
            'analytic_distribution': dict({str(self.analytic_account_id.id): 100.0}) if self.analytic_account_id else False,
            'custom_requisition_line_id': line.id
        }
        return po_line_vals

    def _prepare_po_vals(self, rec, partner):
        return {
            'partner_id': partner.id,
            'currency_id': rec.env.user.company_id.currency_id.id,
            'date_order': fields.Date.today(),
            'company_id': rec.company_id.id,
            'custom_requisition_id': rec.id,
            'origin': rec.name,
        }

    def request_stock(self):
        """Create Purchase Orders from requisition lines"""
        purchase_obj = self.env['purchase.order']
        purchase_line_obj = self.env['purchase.order.line']
        
        for rec in self:
            if not rec.requisition_line_ids:
                raise UserError(_('Please create some requisition lines.'))
            
            po_dict = {}
            for line in rec.requisition_line_ids:
                if line.requisition_type == 'purchase':
                    if not line.partner_id:
                        raise UserError(
                            _('Please enter at least one Vendor on Requisition Lines for Requisition Action Purchase'))
                    for partner in line.partner_id:
                        if partner not in po_dict:
                            po_vals = self._prepare_po_vals(rec, partner)
                            purchase_order = purchase_obj.create(po_vals)
                            po_dict.update({partner: purchase_order})
                            po_line_vals = rec._prepare_po_line(line, purchase_order)
                            purchase_line_obj.sudo().create(po_line_vals)
                        else:
                            purchase_order = po_dict.get(partner)
                            po_line_vals = rec._prepare_po_line(line, purchase_order)
                            purchase_line_obj.sudo().create(po_line_vals)
            rec.state = 'stock'

    def action_done(self):
        """Mark requisition as done"""
        for rec in self:
            rec.date_done = fields.Date.today()
            rec.state = 'done'

    def action_cancel(self):
        """Cancel the requisition"""
        for rec in self:
            rec.state = 'cancel'

    @api.onchange('employee_id')
    def set_department(self):
        for rec in self:
            rec.department_id = rec.employee_id.sudo().department_id.id

    def action_show_po(self):
        """Show related purchase orders"""
        self.ensure_one()
        purchase_action = self.env['ir.actions.act_window']._for_xml_id('purchase.purchase_rfq')
        purchase_action['domain'] = str([('custom_requisition_id', '=', self.id)])
        return purchase_action
