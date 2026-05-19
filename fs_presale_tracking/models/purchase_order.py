from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from markupsafe import Markup
from collections import defaultdict

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    presale_tracking_id = fields.Many2one(
        'presale.tracking',
        string='Presale Tracking',
        readonly=True,
        ondelete='restrict',
        copy=False,
    )
    sourcing_vendor_id = fields.Many2one(
        'res.partner',
        string='Sourcing Vendor',
        domain=[('supplier_rank', '>', 0)],
    )
    is_ecommerce = fields.Boolean(string="Is E-Commerce", default=False, copy=False)
    currency_id = fields.Many2one('res.currency', tracking=True)
    sourcing_markup = fields.Float(
        string='Sourcing Markup (%)', 
        compute='_compute_sourcing_markup', 
        store=True, 
        readonly=True,
        tracking=True
    )
    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('waiting_approval', 'Waiting for Approval'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    purchase_order_type = fields.Selection([
        ('bulk', 'Bulk order')
    ], tracking=True, string='Purchase Order Type', copy=False, )
    action_approve_allowed = fields.Boolean(compute='_compute_action_approve_allowed')
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
    @api.depends('sourcing_vendor_id')
    def _compute_sourcing_markup(self):
        for order in self:
            order.sourcing_markup = 15.0 if order.sourcing_vendor_id else 0.0

    @api.onchange('sourcing_vendor_id')
    def _onchange_sourcing_vendor_id(self):
        # When vendor changes, the markup compute will trigger,
        # but we also need to trigger the line price recalculation instantly in the UI.
        for order in self:
            # We call the markup onchange logic manually to update line prices
            order._onchange_sourcing_markup()

    @api.depends('name', 'partner_ref', 'amount_total', 'currency_id')
    def _compute_display_name(self):
        super()._compute_display_name()
        
        # If we are looking for RFQs in the context of the Link to RFQ Wizard
        tracking_id = self.env.context.get('show_presale_link')
        if tracking_id:
            for order in self:
                if order.presale_tracking_id and order.presale_tracking_id.id == tracking_id:
                    order.display_name = f"✅ {order.display_name} [Current Tracking]"

    def _compute_action_approve_allowed(self):
        is_acc_admin = self.env.user.has_group('account.group_account_manager')
        for order in self:
            allowed = False
            if order.purchase_order_type == 'bulk' and is_acc_admin:
                allowed = True
            order.action_approve_allowed = allowed

    @api.onchange('sourcing_markup')
    def _onchange_sourcing_markup(self):
        for order in self:
            markup_factor = (1 + order.sourcing_markup / 100)
            for line in order.order_line:
                # Prioritize the actual value from the linked Presale Document as the base
                if line.presale_tracking_line_id:
                    base_unit = line.presale_tracking_line_id.list_price
                    base_list = line.presale_tracking_line_id.list_price
                else:
                    # Fallback for manual lines or lines already marked up
                    base_unit = line.price_unit_no_markup or line.price_unit
                    base_list = line.po_list_price_no_markup or (line.po_list_price if hasattr(line, 'po_list_price') else 0.0)

                if order.sourcing_markup > 0:
                    line.price_unit = base_unit * markup_factor
                    if hasattr(line, 'po_list_price'):
                        line.po_list_price = base_list * markup_factor
                else:
                    # Restore original base prices
                    line.price_unit = base_unit
                    if hasattr(line, 'po_list_price'):
                        line.po_list_price = base_list

    def action_request_approval(self):
        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order.write({'state': 'waiting_approval'})

    def action_approve(self):
        is_acc_admin = self.env.user.has_group('account.group_account_manager')
        for order in self:
            if order.purchase_order_type == 'bulk' and not is_acc_admin:
                raise UserError(_("Only Accounting Administrators can approve Bulk Orders."))
            order.button_confirm()

    def button_draft(self):
        for order in self:
            if order.presale_tracking_id and order.presale_tracking_id.state == 'cancel':
                raise UserError(_("You cannot reset this RFQ to draft because the linked Presale Tracking '%s' is cancelled.") % order.presale_tracking_id.name)
        return super(PurchaseOrder, self).button_draft()

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('bypass_presale_track_block'):
            return super(PurchaseOrder, self).create(vals_list)
        for vals in vals_list:
            # 1. Allow if it's an Intercompany Transfer
            partner_id = vals.get('partner_id')
            if partner_id:
                partner = self.env['res.partner'].sudo().browse(partner_id)
                is_intercompany = self.env['res.company'].sudo().search_count([('partner_id', '=', partner.id)]) > 0
                if is_intercompany:
                    continue

            # 2. Block if no Presale Tracking ID and not Bulk
            if not vals.get('presale_tracking_id') and vals.get('purchase_order_type') != 'bulk':
                company_id = vals.get('company_id') or self.env.company.id
                company = self.env['res.company'].browse(company_id)
                if company.is_presale_restricted:
                    # Allow if user is in E-Com Manager group and is_ecommerce is set
                    is_ecom_req = any(v.get('is_ecommerce') for v in vals_list) or self.env.context.get('default_is_ecommerce')
                    if self.env.user.has_group('fs_presale_tracking.group_ecom_sales_manager') and is_ecom_req:
                        continue
                    raise UserError(_(
                        "Manual creation of Purchase Orders is restricted, except in the case of Bulk Orders. "
                        "Please create RFQs through the Presale Tracking module."
                    ))
        return super(PurchaseOrder, self).create(vals_list)

    def write(self, vals):
        if self.env.context.get('bypass_presale_track_block'):
            return super(PurchaseOrder, self).write(vals)
        if 'purchase_order_type' in vals and vals.get('purchase_order_type') != 'bulk':
            for order in self:
                if not order.presale_tracking_id and not vals.get('presale_tracking_id') and order.company_id.is_presale_restricted:
                    # Allow if user is in E-Com Manager group
                    if self.env.user.has_group('fs_presale_tracking.group_ecom_sales_manager'):
                        continue
                    raise UserError(_(
                        "Cannot do Purchase Order without a Presale Tracking link. "
                        "Manual orders possible for 'Bulk order' only."
                    ))
        
        res = super(PurchaseOrder, self).write(vals)
        
        # Sync Vendor/Currency/Sourcing changes back to Presale Tracking
        if not self.env.context.get('presale_sync_from_po') and any(f in vals for f in ['partner_id', 'currency_id', 'sourcing_vendor_id']):
            for order in self:
                if not order.presale_tracking_id:
                    continue
                
                # Update Sourcing Vendor first if changed
                if 'sourcing_vendor_id' in vals:
                    t_lines = order.order_line.mapped('presale_tracking_line_id')
                    if t_lines:
                        t_lines.write({'sourcing_vendor_id': vals.get('sourcing_vendor_id')})

                new_vendor_id = vals.get('partner_id') or order.partner_id.id
                new_currency_id = vals.get('currency_id') or order.currency_id.id
                
                # OPTIMIZATION: Batch processing to avoid N+1 queries and redundant recomputes
                po_lines_with_tracking = order.order_line.filtered(lambda l: l.presale_tracking_line_id)
                if not po_lines_with_tracking:
                    continue

                # 1. Batch search all potential sellers for these products
                tmpl_ids = po_lines_with_tracking.mapped('product_id.product_tmpl_id').ids
                all_sellers = self.env['product.supplierinfo'].sudo().search([
                    ('product_tmpl_id', 'in', tmpl_ids),
                    ('partner_id', '=', new_vendor_id),
                ])
                sellers_by_tmpl = defaultdict(list)
                for s in all_sellers:
                    sellers_by_tmpl[s.product_tmpl_id.id].append(s)

                # 2. Group tracking lines by their new seller_id to batch the writes
                updates_by_seller = defaultdict(list)
                for po_line in po_lines_with_tracking:
                    t_line = po_line.presale_tracking_line_id
                    tmpl_id = po_line.product_id.product_tmpl_id.id
                    
                    # Filter and sort sellers in memory
                    sellers = sellers_by_tmpl.get(tmpl_id, [])
                    best_sellers = [s for s in sellers if s.currency_id.id == new_currency_id or not s.currency_id]
                    best_sellers.sort(key=lambda s: (s.date_start or fields.Date.to_date('1900-01-01'), s.id), reverse=True)
                    
                    match_id = best_sellers[0].id if best_sellers else False
                    updates_by_seller[match_id].append(t_line.id)

                # 3. Perform batched writes (Odoo will handle the necessary recomputes automatically)
                for seller_id, t_line_ids in updates_by_seller.items():
                    self.env['presale.tracking.line'].browse(t_line_ids).with_context(presale_sync_from_po=True).write({
                        'vendor_id': new_vendor_id,
                        'vendor_currency_id': new_currency_id,
                        'seller_id': seller_id
                    })
        
        if 'sourcing_vendor_id' in vals:
            self._onchange_sourcing_markup()
        return res

    def button_confirm(self):
        for order in self:
            if order.sourcing_vendor_id:
                if order.partner_id == order.sourcing_vendor_id:
                    raise UserError(_("The Sourcing Vendor cannot be the same as the Vendor. Please select a different vendor."))
                
                # Validation: Currency must match the Sourcing Vendor's currency
                vendor = order.sourcing_vendor_id
                sourcing_currency = vendor.property_purchase_currency_id or \
                                    (vendor.country_id.currency_id if vendor.country_id else False) or \
                                    order.company_id.currency_id
                
                if order.currency_id != sourcing_currency:
                    raise UserError(_(
                        "The currency of this RFQ (%s) does not match the Sourcing Vendor's currency (%s). "
                        "Please update the currency to match the sourcing vendor before confirming."
                    ) % (order.currency_id.name, sourcing_currency.name))
            # 1. Approval flow for Bulk Orders
            if order.purchase_order_type == 'bulk' and \
               not self.env.user.has_group('account.group_account_manager') and \
               order.state != 'waiting_approval':
                raise UserError(_("Bulk Orders require approval from an Accounting Administrator. Please request approval first."))

        res = super(PurchaseOrder, self).button_confirm()
        
        # Sync logic (existing)
        for order in self:
            if order.presale_tracking_id:
                # Sync po_list_price back to presale line list_price
                for line in order.order_line:
                    if line.presale_tracking_line_id:
                        # Always sync discount back to presale
                        discount = line.po_discount if hasattr(line, 'po_discount') else line.discount
                        line.presale_tracking_line_id.pub_disc = discount

                        # Skip list_price sync back if we have a sourcing markup
                        if order.sourcing_markup > 0:
                            continue
                        
                        current_price = line.price_unit
                        presale_price_unit = line.presale_tracking_line_id.list_price
                        po_price = line.po_list_price if hasattr(line, 'po_list_price') and line.po_list_price else line.price_unit
                        
                        if abs(po_price - presale_price_unit) > 0.01:
                             line.presale_tracking_line_id.list_price = po_price
            
            # State Update Logic
            if order.presale_tracking_id:
                # Check if ALL related POs are confirmed/done
                all_confirmed = all(
                    po.state in ['purchase', 'done'] 
                    for po in order.presale_tracking_id.purchase_order_ids
                )
                if all_confirmed:
                    order.presale_tracking_id.write({'state': 'po_confirmed'})
        return res


    def inter_company_create_sale_order(self, company):
        """ Create a Sales Order from the current PO (self)
            Override of Enterprise method to remove the currency validation between PO and partner pricelist.
        """
        # find user for creating and validation SO/PO from partner company
        intercompany_uid = company.intercompany_user_id and company.intercompany_user_id.id or False
        if not intercompany_uid:
            raise UserError(_(
                'Provide at least one user for inter company relation for %s',
                company.name,
            ))
        # check intercompany user access rights
        if not self.env['sale.order'].has_access('create'):
            raise UserError(_(
                "Inter company user of company %s doesn't have enough access rights",
                company.name,
            ))

        for rec in self:
            # We bypass the check: rec.currency_id.id != company_partner.property_product_pricelist.currency_id.id
            # create the SO and generate its lines from the PO lines
            # read it as sudo, because inter-compagny user can not have the access right on PO
            company_partner = rec.company_id.partner_id.with_user(intercompany_uid)
            sale_order_data = rec.sudo()._prepare_sale_order_data(rec.name, company_partner, company, rec.dest_address_id.id or False)

            # lines are browse as sudo to access all data required to be copied on SO line (mainly for company dependent field like taxes)
            for line in rec.order_line.sudo():
                sale_order_data['order_line'] += [(0, 0, rec._prepare_sale_order_line_data(line, company))]
            sale_order = self.env['sale.order'].with_context(
                allowed_company_ids=company.ids,
                in_rental_app=False,
            ).with_user(intercompany_uid).create(sale_order_data)
            msg = _("Automatically generated from %s of company %s.", rec._get_html_link(), rec.company_id.name)
            sale_order.message_post(body=Markup(msg))
            msg_in_source_po = _("Generated %s in the company %s.", sale_order._get_html_link(), sale_order.company_id.name)
            rec.message_post(body=Markup(msg_in_source_po))

            # write vendor reference field on PO
            if not rec.partner_ref:
                rec.partner_ref = sale_order.name

            # Validation of sales order
            if company.intercompany_document_state == 'posted':
                sale_order.with_user(intercompany_uid).action_confirm()

    def _prepare_sale_order_data(self, name, partner, company, direct_delivery_address):
        """ Override to select a pricelist in the destination company that matches the PO currency """
        res = super()._prepare_sale_order_data(name, partner, company, direct_delivery_address)
        
        # Try to find a pricelist in the destination company that matches the currency of the PO
        target_pricelist = self.env['product.pricelist'].sudo().with_context(allowed_company_ids=company.ids).search([
            ('currency_id', '=', self.currency_id.id),
            ('company_id', 'in', [company.id, False]),
        ], limit=1)
        
        if target_pricelist:
            res['pricelist_id'] = target_pricelist.id
        return res

    @api.model
    def _prepare_sale_order_line_data(self, line, company):
        """ Override to pass the presale tracking line link to the SO line """
        res = super()._prepare_sale_order_line_data(line, company)
        if line.presale_tracking_line_id:
            res.update({'intercompany_presale_tracking_line_id': line.presale_tracking_line_id.id
                        })
        return res


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    presale_tracking_line_id = fields.Many2one(
        'presale.tracking.line',
        string='Presale Tracking Line',
        readonly=True,
        copy=False,
        ondelete='set null',
    )
    # Stable source-of-truth fields for markup calculations
    price_unit_no_markup = fields.Float(string='Unit Price (Base)', digits='Product Price', copy=False)
    po_list_price_no_markup = fields.Float(string='List Price (Base)', digits='Product Price', copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # If creating from a Presale context, capture the initial prices as the "No Markup" base
            if vals.get('presale_tracking_line_id'):
                if 'price_unit' in vals and not vals.get('price_unit_no_markup'):
                    vals['price_unit_no_markup'] = vals['price_unit']
                if 'po_list_price' in vals and not vals.get('po_list_price_no_markup'):
                    vals['po_list_price_no_markup'] = vals['po_list_price']
                    
        if not self.env.context.get('bypass_presale_track_block'):
            for vals in vals_list:
                order_id = vals.get('order_id')
                if order_id:
                    order = self.env['purchase.order'].browse(order_id)
                    if order.presale_tracking_id and order.company_id.is_presale_restricted:
                        # Allow if user is in E-Com Manager group and this is an E-Commerce order
                        if self.env.user.has_group('fs_presale_tracking.group_ecom_sales_manager') and (order.is_ecommerce or vals.get('is_ecommerce')):
                            continue
                        
                        # Bypass for product 500501
                        product_id = vals.get('product_id')
                        if product_id:
                            product = self.env['product.product'].browse(product_id)
                            if product.default_code == '500501':
                                continue

                        raise UserError(_(
                            "Manual addition of lines is restricted for RFQs linked to Presale Tracking. "
                            "Please manage lines through the Presale Tracking document."
                        ))

            # Apply Sourcing Markup if parent order has it
            order_id = vals.get('order_id')
            if order_id:
                order = self.env['purchase.order'].browse(order_id)
                if order.sourcing_markup > 0:
                    markup_factor = 1 + (order.sourcing_markup / 100.0)
                    if 'price_unit' in vals:
                        base_unit = vals.get('price_unit_no_markup', vals['price_unit'])
                        vals['price_unit'] = base_unit * markup_factor
                    if 'po_list_price' in vals:
                        base_list = vals.get('po_list_price_no_markup', vals['po_list_price'])
                        vals['po_list_price'] = base_list * markup_factor

        lines = super().create(vals_list)
        if not self.env.context.get('presale_sync_from_po') and not self.env.context.get('presale_sync_from_so'):
            for line in lines:
                if line.presale_tracking_line_id:
                    line._sync_back_to_presale_tracking()
        return lines

    @api.depends('product_qty', 'product_uom_id', 'company_id', 'order_id.partner_id')
    def _compute_price_unit_and_date_planned_and_name(self):
        # Capture current po_discount values before they get potentially overwritten
        # because 'discount' is related to 'po_discount' and standard compute writes to 'discount'.
        saved_discounts = {line.id: line.po_discount for line in self if line.id}
        
        super()._compute_price_unit_and_date_planned_and_name()
        
        for line in self:
            if line.id in saved_discounts:
                # If we are in any sync context OR if we explicitly want to preserve manual overrides
                # (which is usually the case when using po_discount).
                # We restore the discount if the standard compute changed it back to default.
                if line.po_discount != saved_discounts[line.id]:
                     # Only restore if it was a revert to seller's default (65.0 example) 
                     # but we had something else (40.0 example).
                     # For now, we trust po_discount more.
                     line.po_discount = saved_discounts[line.id]

    def unlink(self):
        if not self.env.context.get('bypass_presale_track_block'):
            for line in self:
                if line.order_id.presale_tracking_id and line.order_id.company_id.is_presale_restricted:
                    # Bypass for product 500501 - Shipping product
                    if line.product_id.default_code == '500501':
                        continue
                    raise UserError(_(
                        "Manual deletion of lines is restricted for RFQs linked to Presale Tracking. "
                        "Please manage lines through the Presale Tracking document."
                    ))
        return super().unlink()

    def write(self, vals):
        res = super().write(vals)
        
        # Trigger synchronization back to Presale Tracking if relevant fields updated
        if not self.env.context.get('presale_sync_from_po') and not self.env.context.get('presale_sync_from_so'):
            sync_fields = ['product_qty', 'rfq_qty', 'po_qty', 'po_list_price', 'po_discount', 'discount', 'price_unit', 'product_id']
            if any(f in vals for f in sync_fields):
                for line in self:
                    if line.presale_tracking_line_id:
                        line._sync_back_to_presale_tracking(vals)
        return res

    def _sync_back_to_presale_tracking(self, vals=None):
        """Helper to push PO line changes back to the linked tracking line"""
        self.ensure_one()
        if not self.presale_tracking_line_id:
            return
            
        # Ensure vals is a dict before any checks
        if vals is None:
            vals = {}
            
        # Skip price synchronization if order has a sourcing markup
        if self.order_id.sourcing_markup > 0:
            # Check if any non-price fields are being updated
            sync_fields = ['product_qty', 'rfq_qty', 'po_qty', 'po_discount', 'discount']
            if not any(f in vals for f in sync_fields):
                return
            
        # Prepare values for tracking line
        # Use vals if available, otherwise fallback to record value
        list_price = vals.get('po_list_price', self.po_list_price if hasattr(self, 'po_list_price') else self.price_unit)
        t_line = self.presale_tracking_line_id
        t_vals = {}
        
        # Only sync if the field is actually in vals (avoiding stale cache reversions)
        if 'po_list_price' in vals:
            po_list_price = vals.get('po_list_price')
            # For list_price, we compare against t_line.list_price
            if po_list_price is not None and abs(t_line.list_price - po_list_price) > 0.01:
                t_vals['list_price'] = po_list_price

        if 'po_discount' in vals or 'discount' in vals:
            discount = vals.get('po_discount') if 'po_discount' in vals else vals.get('discount')
            if discount is not None and abs(t_line.pub_disc - discount) > 0.01:
                t_vals['pub_disc'] = discount
        
        if 'price_unit' in vals:
            price_unit = vals.get('price_unit')
            if price_unit is not None and abs(t_line.unit_price - price_unit) > 0.01:
                t_vals['unit_price'] = price_unit

        quantity = None
        if 'rfq_qty' in vals:
            quantity = vals.get('rfq_qty')
        elif 'product_qty' in vals:
            quantity = vals.get('product_qty')
            
        if quantity is not None and abs(t_line.qty - (quantity or 0.0)) > 0.01:
            t_vals['qty'] = quantity
            
        # Double check: remove price fields from t_vals if markup is present
        if self.order_id.sourcing_markup > 0:
            t_vals.pop('list_price', None)
            t_vals.pop('unit_price', None)
            # We keep 'pub_disc' as requested

        if t_vals:
            t_line.with_context(presale_sync_from_po=True).write(t_vals)
