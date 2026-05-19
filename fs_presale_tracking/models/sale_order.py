from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    presale_tracking_id = fields.Many2one(
        'presale.tracking',
        string='Presale Tracking',
        readonly=True,
        ondelete='restrict',
        help="The presale tracking document from which this order was created"
    )
    is_ecommerce = fields.Boolean(string="Is E-Commerce", default=False, copy=False)
    is_sample_so = fields.Boolean(string="Is Sample SO", default=False, copy=False)
    is_intercompany = fields.Boolean(compute='_compute_is_intercompany', string="Is Intercompany")
    rfq_exists = fields.Boolean(compute='_compute_rfq_exists', string="RFQ Created")

    @api.depends('partner_id')
    def _compute_is_intercompany(self):
        company_partners = self.env['res.company'].sudo().search([]).mapped('partner_id.id')
        for order in self:
            order.is_intercompany = order.partner_id.id in company_partners

    def _compute_rfq_exists(self):
        for order in self:
            # Check if any PO line (not cancelled) is linked to this SO
            count = self.env['purchase.order.line'].sudo().search_count([
                ('related_so', '=', order.id),
                ('state', '!=', 'cancel')
            ])
            order.rfq_exists = count > 0

    def action_create_purchase_rfqs_intercom(self):
        """Feature: Open wizard to create a single PO for a selected vendor"""
        self.ensure_one()
        if not self.is_intercompany:
            raise UserError(_("This action is only available for inter-company orders."))
        
        if self.rfq_exists:
            raise UserError(_("A Purchase Quotation has already been created for this order."))

        return {
            'name': _('Create Purchase RFQ'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.create.rfq.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'default_vendor_id': self.auto_purchase_order_id.sourcing_vendor_id.id,
            }
        }

    def action_view_presale_tracking(self):
        """Action for smart button to jump to tracker"""
        self.ensure_one()
        if not self.presale_tracking_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'presale.tracking',
            'view_mode': 'form',
            'res_id': self.presale_tracking_id.id,
            'target': 'current',
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # 1. Allow if it's an Intercompany Transfer
            # Check if the partner is actually a company defined in the system
            partner_id = vals.get('partner_id')
            if partner_id:
                partner = self.env['res.partner'].sudo().browse(partner_id)
                is_intercompany = self.env['res.company'].sudo().search_count([('partner_id', '=', partner.id)]) > 0
                if is_intercompany:
                    continue

            # 2. Block if no Presale Tracking ID (unless it's a Sample SO created from the specific menu)
            if not vals.get('presale_tracking_id'):
                # Handle Sample SO logic first
                if self.env.context.get('from_sample_so_menu') or vals.get('is_sample_so'):
                    company_id = vals.get('company_id') or self.env.company.id
                    if self.env.user.sample_so_company_ids and company_id not in self.env.user.sample_so_company_ids.ids:
                        raise UserError(_("You are not allowed to create Sample SOs for this company."))
                    # If valid sample SO, bypass the presale tracking block
                    continue

                # Normal SO case without Presale Tracking ID
                company_id = vals.get('company_id') or self.env.company.id
                company = self.env['res.company'].browse(company_id)
                if company.is_presale_restricted:
                    # Allow if user is in E-Com Manager group and is_ecommerce is set
                    is_ecom_req = any(v.get('is_ecommerce') for v in vals_list) or self.env.context.get('default_is_ecommerce')
                    if self.env.user.has_group('fs_presale_tracking.group_ecom_sales_manager') and is_ecom_req:
                        continue
                    raise UserError(_(
                        "Manual creation of Sale Orders is restricted. "
                        "Please create Sale Orders through the Presale Tracking module."
                    ))
        return super(SaleOrder, self).create(vals_list)

    def action_draft(self):
        for order in self:
            if order.presale_tracking_id and order.presale_tracking_id.state == 'cancel':
                raise UserError(_("You cannot reset this Sale Order to draft because the linked Presale Tracking '%s' is cancelled.") % order.presale_tracking_id.name)
        return super(SaleOrder, self).action_draft()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    presale_tracking_line_id = fields.Many2one(
        'presale.tracking.line',
        string='Presale Tracking Line',
        readonly=True,
        copy=False,
        ondelete='set null',
    )
    intercompany_presale_tracking_line_id = fields.Many2one(
        'presale.tracking.line',
        string='Intercompany Presale Tracking Line',
        readonly=True,
        copy=False,
        ondelete='set null',
    )
    presale_vendor_id = fields.Many2one(
        'res.partner',
        string='Presale Vendor',
        readonly=True,
        copy=False,
        ondelete='set null',
    )

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.context.get('bypass_presale_track_block'):
            for vals in vals_list:
                order_id = vals.get('order_id')
                if order_id:
                    order = self.env['sale.order'].browse(order_id)
                    if not order.is_sample_so and order.presale_tracking_id and order.company_id.is_presale_restricted:
                        # Allow if it's the specific discount product configured in the company
                        if order.company_id.sale_discount_product_id and vals.get('product_id') == order.company_id.sale_discount_product_id.id:
                            continue

                        # Allow if user is in E-Com Manager group and this is an E-Commerce order
                        if self.env.user.has_group('fs_presale_tracking.group_ecom_sales_manager') and (order.is_ecommerce or vals.get('is_ecommerce')):
                            continue
                        raise UserError(_(
                            "Manual addition of lines is restricted for orders linked to Presale Tracking. "
                            "Please manage lines through the Presale Tracking document."
                        ))

        lines = super().create(vals_list)
        if not self.env.context.get('presale_sync_from_po') and not self.env.context.get('presale_sync_from_so'):
            for line in lines:
                if line.presale_tracking_line_id:
                    line._sync_back_to_presale_tracking()
        return lines

    def unlink(self):
        if not self.env.context.get('bypass_presale_track_block'):
            for line in self:
                if not line.order_id.is_sample_so and line.order_id.presale_tracking_id and line.order_id.company_id.is_presale_restricted:
                    # Allow deletion if it's the specific discount product configured in the company
                    if line.company_id.sale_discount_product_id and line.product_id == line.company_id.sale_discount_product_id:
                        continue
                        
                    raise UserError(_(
                        "Manual deletion of lines is restricted for orders linked to Presale Tracking. "
                        "Please manage lines through the Presale Tracking document."
                    ))
        return super().unlink()

    def write(self, vals):
        res = super().write(vals)
        # Capture current sync context to preserve the chain
        ctx = self.env.context
        from_presale = ctx.get('presale_sync_from_po') or ctx.get('presale_sync_from_so')
        
        if not from_presale:
            sync_fields = ['product_uom_qty', 'so_qty', 'so_quantity', 'price_unit']
            if any(f in vals for f in sync_fields):
                for line in self:
                    if line.presale_tracking_line_id:
                        line._sync_back_to_presale_tracking()
        return res

    def _sync_back_to_presale_tracking(self):
        """Helper to push SO line changes back to the linked tracking line"""
        self.ensure_one()
        if not self.presale_tracking_line_id:
            return
            
        t_line = self.presale_tracking_line_id
        t_vals = {}
        
        # Determine quantity (respecting custom fields if present)
        quantity = self.product_uom_qty
        if hasattr(self, 'so_qty') and self.so_qty:
            quantity = self.so_qty
            
        if abs(t_line.unit_price - self.price_unit) > 0.01:
            t_vals['unit_price'] = self.price_unit
        if abs(t_line.qty - quantity) > 0.01:
            t_vals['qty'] = quantity
            
        if t_vals:
            # Preserve the full context chain (if we came from PO, tell Presale we are still in that chain)
            sync_ctx = {'presale_sync_from_so': True}
            if self.env.context.get('presale_sync_from_po'):
                sync_ctx['presale_sync_from_po'] = True
                
            t_line.with_context(**sync_ctx).write(t_vals)
