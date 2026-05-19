import base64
import csv
import io
import xlsxwriter
from datetime import timedelta

from odoo import api, fields, models, _
from markupsafe import Markup
from odoo.exceptions import UserError


class PresaleTracking(models.Model):
    _name = 'presale.tracking'
    _description = 'Presale Tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Name',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    reference = fields.Char(string="Reference", copy=False, tracking=True)
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('rfq_created', 'RFQ Created'),
        ('po_confirmed', 'All PO Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, copy=False)
    
    line_ids = fields.One2many(
        'presale.tracking.line',
        'tracking_id',
        string='Tracking Lines',
    )
    notes = fields.Html(string='Notes')
    
    # Attachment for Request
    request_file = fields.Binary(string='Initial Inquiry Document', copy=False, attachment=True)
    request_filename = fields.Char(string='Filename', copy=False,)
    enquiry_date = fields.Date(string='Inquiry Date', copy=False,)

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        tracking=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        compute='_compute_currency_id',
        store=True,
    )
    pricelist_id = fields.Many2one(
        'product.pricelist', 
        string='Pricelist', 
        check_company=True, 
        required=True,
        compute='_compute_pricelist_id',
        store=True,
        readonly=False,
        tracking=True,
        help="Pricelist used for Sale Order creation and Unit Price calculation."
    )
    customer_currency_id = fields.Many2one(
        'res.currency',
        string='Customer Currency',
        compute='_compute_customer_currency_id',
        store=True,
    )

    @api.depends('partner_id')
    def _compute_pricelist_id(self):
        for record in self:
            if record.partner_id and not record.pricelist_id:
                record.pricelist_id = record.partner_id.property_product_pricelist
            elif not record.partner_id:
                record.pricelist_id = False

    @api.depends('pricelist_id')
    def _compute_customer_currency_id(self):
        for record in self:
            record.customer_currency_id = record.pricelist_id.currency_id

    @api.depends('company_id')
    def _compute_currency_id(self):
        for record in self:
            record.currency_id = record.company_id.currency_id or self.env.company.currency_id

    
    # Computed totals
    total_qty = fields.Integer(
        string='Total Quantity',
        compute='_compute_totals',
        store=True,
    )
    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_totals',
        store=True,
        digits='Product Price',
    )
    total_amount_usd = fields.Float(
        string='Total Amount (USD)',
        compute='_compute_totals',
        store=True,
        digits='Product Price',
    )
    line_count = fields.Integer(
        string='Line Count',
        compute='_compute_totals',
        store=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Customer Quotation',
        readonly=True,
    )

    has_unlinked_po_lines = fields.Boolean(compute='_compute_links_status', store=True)
    has_unlinked_so_lines = fields.Boolean(compute='_compute_links_status', store=True)

    @api.depends('line_ids.is_linked_to_po', 'line_ids.product_id', 'sale_order_id.order_line.presale_tracking_line_id', 'line_ids.is_so_up_to_date')
    def _compute_links_status(self):
        for record in self:
            unlinked_po = any(not l.is_linked_to_po for l in record.line_ids)
            
            # Strict 1:1 SO check: A line is "linked" if its ID is in the SO lines' tracking link
            so_line_track_ids = set(record.sale_order_id.order_line.mapped('presale_tracking_line_id.id')) if record.sale_order_id else set()
            unlinked_so = False
            for line in record.line_ids:
                if not line.product_id:
                    # Lines without products are considered unlinked if there's an SO
                    if record.sale_order_id:
                        unlinked_so = True
                    continue
                if line.id not in so_line_track_ids or not line.is_so_up_to_date:
                    unlinked_so = True
                    break
            
            record.has_unlinked_po_lines = unlinked_po
            record.has_unlinked_so_lines = unlinked_so


    # Sale Order Link
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Customer Quotation',
        readonly=True,
        copy=False,
    )

    sale_order_count = fields.Integer(
        string='Sale Orders',
        compute='_compute_sale_order_count',
    )
    
    # Purchase Order Link
    purchase_order_ids = fields.One2many(
        'purchase.order',
        'presale_tracking_id', # Note: We need to add this field to purchase.order or use a compute if not adding relation there
        string='Purchase Orders',
    )
    purchase_order_count = fields.Integer(
        string='Purchase Order Count',
        compute='_compute_purchase_order_count',
    )
    


    missing_lines_count = fields.Integer(
        string='Missing Lines',
        compute='_compute_missing_lines_count',
        store=True,
    )

    # Analytics / Dashboard Fields
    rfq_created_date = fields.Datetime(string='RFQ Creation Date', readonly=True)
    so_created_date = fields.Datetime(string='SO Creation Date', readonly=True)
    po_confirmed_date = fields.Datetime(string='PO Confirmed Date', readonly=True)
    
    duration_to_rfq = fields.Float(
        string='Days to RFQ', 
        compute='_compute_durations', 
        store=True,
        help="Days from Presale Creation to RFQ Creation"
    )
    duration_rfq_to_so = fields.Float(
        string='Days RFQ to SO', 
        compute='_compute_durations', 
        store=True,
        help="Days from RFQ Creation to SO Creation"
    )
    duration_to_confirm = fields.Float(
        string='Days to Confirm', 
        compute='_compute_durations', 
        store=True,
        help="Days from RFQ Creation to PO Confirmation"
    )
    
    @api.depends('create_date', 'rfq_created_date', 'so_created_date', 'po_confirmed_date')
    def _compute_durations(self):
        for record in self:
            # Helper to diff timestamps in days
            def diff_days(start, end):
                if not start or not end:
                    return 0.0
                delta = end - start
                return round(delta.total_seconds() / 86400, 2)

            record.duration_to_rfq = diff_days(record.create_date, record.rfq_created_date)
            record.duration_rfq_to_so = diff_days(record.rfq_created_date, record.so_created_date)
            
            # For confirmation, we measure from RFQ creation to Confirmation
            record.duration_to_confirm = diff_days(record.rfq_created_date, record.po_confirmed_date)

    @api.depends('line_ids', 'line_ids.product_id')
    def _compute_missing_lines_count(self):
        for record in self:
            record.missing_lines_count = len(record.line_ids.filtered(lambda l: not l.product_id))

    @api.depends('sale_order_id', 'sale_order_id.state')
    def _compute_sale_order_count(self):
        for record in self:
            record.sale_order_count = 1 if record.sale_order_id and record.sale_order_id.state != 'cancel' else 0

    @api.depends('line_ids.purchase_order_line_ids', 'purchase_order_ids', 'purchase_order_ids.state')
    def _compute_purchase_order_count(self):
        for record in self:
            # Combine POs linked via lines and those linked via the header field
            line_pos = record.line_ids.mapped('purchase_order_line_ids.order_id')
            header_pos = record.purchase_order_ids
            # Filter for non-cancelled POs to give an accurate 'active' count
            connected_pos = (line_pos | header_pos).filtered(lambda po: po.state != 'cancel')
            record.purchase_order_count = len(connected_pos)

    @api.depends('line_ids', 'line_ids.qty', 'line_ids.total_amount', 'line_ids.total_usd')
    def _compute_totals(self):
        for record in self:
            record.total_qty = sum(record.line_ids.mapped('qty'))
            record.total_amount = sum(record.line_ids.mapped('total_amount'))
            record.total_amount_usd = sum(record.line_ids.mapped('total_usd'))
            record.line_count = len(record.line_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = _('New')
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        # Auto-start progress if in draft, file attached, and lines exist
        if 'request_file' in vals or 'line_ids' in vals or 'enquiry_date' in vals: 
            for record in self:
                if record.state == 'draft' and record.request_file and record.line_ids and record.enquiry_date:
                    record.action_in_progress()
        return res
    
    def unlink(self):
        for record in self:
            if record.state not in ['draft', 'cancel']:
                raise UserError(_(
                    "You cannot delete a Presale Tracking record that is in state '%s'. "
                    "Please cancel it first to acknowledge the workflow termination."
                ) % record.state)
            
            # PROHIBIT deletion if ANY record was ever connected, to close the loophole.
            if record.sale_order_id or record.purchase_order_ids:
                raise UserError(_(
                    "Cannot delete Presale Tracking '%s' because it is linked to a Sale Order or Purchase Orders. "
                    "To maintain workflow integrity and audit history, please 'Cancel' this record instead of deleting it."
                ) % record.name)
        
        return super(PresaleTracking, self).unlink()

    def action_cancel(self):
        for record in self:
            # 1. Check Sale Order
            if record.sale_order_id and record.sale_order_id.state != 'cancel':
                raise UserError(_(
                    "Cannot cancel Presale Tracking '%s' because it is linked to an active Sale Order (%s). "
                    "Please cancel the Sale Order first."
                ) % (record.name, record.sale_order_id.name))
            
            # 2. Check Purchase Orders
            active_pos = record.purchase_order_ids.filtered(lambda po: po.state != 'cancel')
            if active_pos:
                po_names = ", ".join(active_pos.mapped('name'))
                raise UserError(_(
                    "Cannot cancel Presale Tracking '%s' because it is linked to active Purchase Orders (%s). "
                    "Please cancel the Purchase Orders first."
                ) % (record.name, po_names))
        
        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_in_progress(self):
        if not self.request_file or not self.enquiry_date:
            raise UserError(_('Please attach the Request Document and set Enquiry Date before starting progress.'))
            
        if self.name == _('New'):
            self.name = self.env['ir.sequence'].next_by_code('presale.tracking') or _('New')
            
        self.write({'state': 'in_progress'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_rescan_products(self):
        """Rescan lines without products to try and match them by ISBN"""
        self.ensure_one()
        lines_to_check = self.line_ids.filtered(lambda l: not l.product_id and l.isbn)
        if not lines_to_check:
            return
        
        # Batch search
        isbns = lines_to_check.mapped('isbn')
        products = self.env['product.product'].search([('default_code', 'in', isbns)])
        product_map = {p.default_code: p.id for p in products}
        
        matched_count = 0
        for line in lines_to_check:
            if line.isbn in product_map:
                line.product_id = product_map[line.isbn]
                matched_count += 1
        
        if matched_count:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Rescan Complete'),
                    'message': _('%d products matched and linked.') % matched_count,
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                }
            }
        else:
             return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Rescan Complete'),
                    'message': _('No new matches found.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

    def _generate_missing_product_report(self, lines):
        """Helper to generate Excel report for missing products"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Missing Products')
        
        # Formats
        bold_yellow = workbook.add_format({
            'bold': True,
            'bg_color': '#FFFF00', # Yellow
            'border': 1
        })
        bold_white = workbook.add_format({
            'bold': True,
            'border': 1
        })
        
        # All Headers (Product Import Template)
        headers = [
            'Item Code', 'Item Name', 'Item Category', 'Cost Price', 'Weight In (KG)', 
            'Selling Price', 'Author', 'Publisher', 'Master Publisher', 'Uk Wholesaler', 
            'Non-Uk Wholesalers', 'Publication Country', 'Main Title', 'Subtitle', 'Subject', 
            'Pages', 'Edition', 'Series', 'Book Language', 'Product Format', 
            'Interest Age', 'Audience Readership', 'Publication Date', 'Status', 
            'Height Along Spine In Mm', 'Width From Spine To Edge In Mm', 'Product Type', 
            'Can be sold', 'Can be purchased', 'Available in POS', 'Customer Taxes', 'Vendor Taxes'
        ]

        # Headers to Highlight Yellow
        yellow_headers = [
            'Item Code', 'Item Name', 'Item Category', 'Weight In (KG)', 'Publisher',
            'Product Format', 'Product Type', 'Customer Taxes', 'Vendor Taxes'
        ]
        
        # Set Column Width
        sheet.set_column(0, len(headers)-1, 25)

        # Write Headers with Conditional Formatting
        for col_num, header in enumerate(headers):
            style = bold_yellow if header in yellow_headers else bold_white
            sheet.write(0, col_num, header, style)
        
        # Write Data
        for i, line in enumerate(lines, 1):
            # Item Code (ISBN)
            sheet.write(i, 0, line.isbn or '')
            # Item Name (Empty as requested)
            sheet.write(i, 1, '')
            # Other columns left empty as per requirement (template for import)
        
        workbook.close()
        output.seek(0)
        return output.read()

    def action_download_missing_report(self):
        """Generate and download missing products report"""
        self.ensure_one()
        lines_without_product = self.line_ids.filtered(lambda l: not l.product_id)
        
        if not lines_without_product:
            raise UserError(_('No missing products found.'))

        file_content = self._generate_missing_product_report(lines_without_product)
        
        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': 'missing_products.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(file_content),
            'res_model': 'presale.tracking',
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    def action_export_template(self):
        """Export a CSV template with ISBN and QTY headers"""
        self.ensure_one()
        
        # Create CSV content with headers
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = ['ISBN', 'QTY']
        writer.writerow(headers)
        
        if self.line_ids:
            # Export existing lines
            for line in self.line_ids:
                writer.writerow([line.isbn, line.qty])
        else:
            # Add a sample row if no lines exist
            writer.writerow(['978-0-123456-47-2', '10'])
        
        # Prepare file for download
        csv_content = output.getvalue()
        output.close()
        
        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': 'presale_tracking_template.csv',
            'type': 'binary',
            'datas': base64.b64encode(csv_content.encode('utf-8')),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'text/csv',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    def action_update_tracking_lines(self):
        """Open the update tracking lines wizard"""
        self.ensure_one()
        return {
            'name': _('Update Tracking Lines'),
            'type': 'ir.actions.act_window',
            'res_model': 'presale.tracking.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_tracking_id': self.id,
            },
        }

    def action_view_lines(self):
        """Open tracking lines in list view with multi-edit enabled"""
        self.ensure_one()
        return {
            'name': _('Tracking Lines - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'presale.tracking.line',
            'view_mode': 'list',
            'domain': [('tracking_id', '=', self.id)],
            'context': {
                'default_tracking_id': self.id,
            },
        }



    def action_create_purchase_rfqs(self):
        """Action: Open Confirmation Wizard"""
        self.ensure_one()
        
        # 1. Validation
        lines_missing_vendor = self.line_ids.filtered(lambda l: not l.vendor_id)
        if lines_missing_vendor:
            raise UserError(_("Some lines do not have a Vendor assigned. Please assign vendors or rescan before creating RFQs."))

        lines_missing_product = self.line_ids.filtered(lambda l: not l.product_id)
        if lines_missing_product:
            raise UserError(_("Some lines do not have a mapped Product. Please rescan products or assign them manually."))

        # 2. Group by Vendor for Summary (Only Unlinked Lines)
        unlinked_lines = self.line_ids.filtered(lambda l: not l.is_linked_to_po)
        if not unlinked_lines:
            raise UserError(_("All lines are already linked to RFQs/POs."))
            
        grouped_lines = {}
        for line in unlinked_lines:
            key = (line.vendor_id, line.vendor_currency_id, line.sourcing_vendor_id)
            if key not in grouped_lines:
                grouped_lines[key] = []
            grouped_lines[key].append(line)

        # 3. Prepare Wizard Values
        summary_vals = []
        for (vendor, currency, sourcing_vendor), lines in grouped_lines.items():
            total_amount = sum(l.list_price * l.qty for l in lines) # Approx total based on list price
            total_qty = sum(l.qty for l in lines)
            summary_vals.append((0, 0, {
                'vendor_id': vendor.id,
                'sourcing_vendor_id': sourcing_vendor.id if sourcing_vendor else False,
                'currency_id': currency.id if currency else self.company_id.currency_id.id,
                'line_count': len(lines),
                'total_qty': total_qty,
                'amount_total': total_amount,
            }))
            
        return {
            'name': _('Confirm Purchase RFQs'),
            'type': 'ir.actions.act_window',
            'res_model': 'presale.create.rfq.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_presale_tracking_id': self.id,
                'default_summary_ids': summary_vals,
            }
        }

    def _create_purchase_rfqs_from_grouping(self):
        """Actual Creation Logic called by Wizard"""
        self.ensure_one()
        
        # Re-group (Only Unlinked Lines)
        unlinked_lines = self.line_ids.filtered(lambda l: not l.is_linked_to_po)
        if not unlinked_lines:
            return  # Or handle as error
            
        grouped_lines = {}
        for line in unlinked_lines:
            key = (line.vendor_id, line.vendor_currency_id, line.sourcing_vendor_id)
            if key not in grouped_lines:
                grouped_lines[key] = []
            grouped_lines[key].append(line)

        # Create POs
        created_pos = self.env['purchase.order']
        
        # Tag the Post Sales Project enabled
        tracking_project = self.env['project.project'].search([('sale_tracking','=',True),('active','=',True)],
                                                              limit=1)
        if not tracking_project:
            raise ValueError("Tracking Project not set")
        # Early-Create Sale Order (Quotation) if not exists
        if not self.sale_order_id:
            sale_order = self.env['sale.order'].create(
                {
                'partner_id': self.partner_id.id,
                'pricelist_id': self.pricelist_id.id,
                'company_id': self.company_id.id,
                'origin': self.name,
                'presale_tracking_id': self.id,
                'tracking_project_id': tracking_project.id,
            })
            self.sale_order_id = sale_order.id
            self.so_created_date = fields.Datetime.now()
            sale_order.message_post(body=_("Created from the Presale tracker %s") % self.name)
        else:
            sale_order = self.sale_order_id


        for (vendor, currency, sourcing_vendor), lines in grouped_lines.items():
            po_vals = {
                'partner_id': vendor.id,
                'sourcing_vendor_id': sourcing_vendor.id if sourcing_vendor else False,
                'currency_id': currency.id if currency else self.company_id.currency_id.id,
                'company_id': self.company_id.id,
                'origin': self.name,
                'presale_tracking_id': self.id, # Link back
                'date_order': fields.Date.today(),
            }
            
            po = self.env['purchase.order'].create(po_vals)
            po.message_post(body=_("Created from the Presale tracker %s") % self.name)
            created_pos += po
            
            # Create PO Lines
            for line in lines:
                # Map fields
                price_unit = line.list_price # Presale List Price -> PO Price Unit
                vals = {
                    'order_id': po.id,
                    'product_id': line.product_id.id,
                    'name': line.product_id.name or line.title,
                    'product_qty': line.qty,
                    'product_uom_id': line.product_id.uom_id.id,
                    'price_unit': price_unit,
                    'price_unit_no_markup': price_unit,
                    'po_list_price': price_unit,
                    'po_list_price_no_markup': price_unit,
                    'po_discount': line.pub_disc, # Mapping pub_disc to po_discount
                    'discount': line.pub_disc, # Mapping pub_disc to discount
                    'date_planned': fields.Date.today(),
                    'presale_tracking_line_id': line.id, # Link for sync
                    'rfq_qty': line.qty, 
                    'po_qty': line.qty,
                    'related_so': sale_order.id, # Link to the Customer Quotation
                }
                self.env['purchase.order.line'].with_context(bypass_presale_track_block=True).create(vals)

        # Automatically sync lines to Sale Order
        self.action_sync_sale_order_lines()

        # Update state and timestamp
        self.write({
            'state': 'rfq_created',
            'rfq_created_date': fields.Datetime.now()
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('RFQs Created'),
                'message': _('%d Request for Quotations created successfully.') % len(created_pos),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            }
        }

    def action_view_purchase_orders(self):
        self.ensure_one()
        # Union of POs linked via lines and header, excluding cancelled ones
        connected_pos = (self.line_ids.mapped('purchase_order_line_ids.order_id') | self.purchase_order_ids).filtered(lambda po: po.state != 'cancel')
        return {
            'name': _('Purchase Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'views': [
                (self.env.ref('purchase.purchase_order_view_tree').id, 'list'),
                (self.env.ref('purchase.purchase_order_form').id, 'form'),
            ],
            'domain': [('id', 'in', connected_pos.ids)],
            'context': {'default_presale_tracking_id': self.id},
        }

    def action_sync_sale_order_lines(self):
        """Update/Create sale order lines from presale tracking lines.
           Automatically handles attachment copying without duplicates.
        """
        self.ensure_one()
        # If no lines exist and no SO is linked, nothing to do
        if not self.line_ids and not self.sale_order_id:
            return
        
        # 1. Validation Logic
        lines_without_product = self.line_ids.filtered(lambda l: not l.product_id)
        if lines_without_product and not self.env.context.get('skip_validation'):
            # If we are in RFQ flow, we might want to just skip these lines rather than block entirely,
            # but the existing logic blocks the user. Let's maintain safety.
            file_content = self._generate_missing_product_report(lines_without_product)
            attachment = self.env['ir.attachment'].create({
                'name': 'missing_products_for_quote.xlsx',
                'type': 'binary',
                'datas': base64.b64encode(file_content),
                'res_model': 'presale.tracking',
                'res_id': self.id,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            })
            
            raise UserError(_('%d lines have missing products. Quotation synchronization deferred. Downloaded report in attachments.') % len(lines_without_product))

        # 2. Sale Order Header (Ensure exists if there are lines to sync)
        if not self.sale_order_id:
            if not self.line_ids:
                return
            # Tag the Post Sales Project enabled
            tracking_project = self.env['project.project'].search([('sale_tracking','=',True),('active','=',True)],
                                                                  limit=1)
            sale_order = self.env['sale.order'].create({
                'partner_id': self.partner_id.id,
                'pricelist_id': self.pricelist_id.id,
                'company_id': self.company_id.id,
                'origin': self.name,
                'presale_tracking_id': self.id,
                'tracking_project_id': tracking_project.id if tracking_project else False,
            })
            self.sale_order_id = sale_order.id
            sale_order.message_post(body=_("Created from the Presale tracker %s") % self.name)
            self.so_created_date = fields.Datetime.now()
        else:
            sale_order = self.sale_order_id

        # 2.1. Check if SO is confirmed
        if sale_order.state in ['sale', 'done']:
            # Log a small message or just return. Returning a notification is more user-friendly.
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sync Blocked'),
                    'message': _('The linked Sale Order is already confirmed. Changes to the tracker will not be synced to maintain audit integrity.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        # 3. Create/Update Sale Order Lines (Strict 1:1 Mapping)
        # Flush tracking lines to ensure latest values are used
        self.line_ids.flush_recordset(['qty', 'product_id', 'unit_price', 'title'])
        
        # Identify current tracking line IDs
        current_tracking_line_ids = set(self.line_ids.ids)
        discount_product_id = self.company_id.sale_discount_product_id.id if self.company_id.sale_discount_product_id else False

        # 3.1. Cleanup: Delete SO lines that are no longer in this tracker
        so_lines_to_delete = sale_order.order_line.filtered(
            lambda l: (l.presale_tracking_line_id and l.presale_tracking_line_id.id not in current_tracking_line_ids) or
                      (not l.presale_tracking_line_id and l.product_id.id != discount_product_id) # Cleanup legacy aggregated lines
        )
        if so_lines_to_delete:
            so_lines_to_delete.with_context(bypass_presale_track_block=True).unlink()

        # 3.2. Sync individual lines
        for line in self.line_ids:
            if not line.product_id:
                continue
                
            existing_so_line = self.env['sale.order.line'].search([
                ('order_id', '=', sale_order.id),
                ('presale_tracking_line_id', '=', line.id)
            ], limit=1)
            
            so_vals = {
                'order_id': sale_order.id,
                'product_id': line.product_id.id,
                'name': line.title or line.product_id.name,
                'product_uom_qty': line.qty,
                'so_qty': line.qty,
                'so_quantity': line.qty,
                'price_unit': line.unit_price,
                'presale_tracking_line_id': line.id,
                'presale_vendor_id': line.vendor_id.id if line.vendor_id else False,
            }
            
            if not existing_so_line:
                if 'list_price' in self.env['sale.order.line']._fields:
                    so_vals['list_price'] = line.unit_price
                self.env['sale.order.line'].with_context(bypass_presale_track_block=True).create(so_vals)
            else:
                if 'list_price' in existing_so_line._fields:
                    so_vals['list_price'] = line.unit_price
                existing_so_line.with_context(bypass_presale_track_block=True).write(so_vals)
            
            line.write({'is_so_up_to_date': True})

        # 4. Smart Attachment Copy (De-duplicated)
        tracking_attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'presale.tracking'),
            ('res_id', '=', self.id),
        ])
        existing_so_attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', sale_order.id),
        ])
        
        # Simple de-duplication by name and size
        existing_keys = set((a.name, a.file_size) for a in existing_so_attachments)
        
        for att in tracking_attachments:
            if (att.name, att.file_size) not in existing_keys:
                att.copy({
                    'res_model': 'sale.order',
                    'res_id': sale_order.id,
                })

        # 5. Log activity
        so_link = Markup("<a href='#' data-oe-model='sale.order' data-oe-id='{}'>{}</a>").format(sale_order.id, sale_order.name)
        msg = Markup(_('Sale Order {} synchronized with tracking lines and attachments.')).format(so_link)
        self.message_post(body=msg)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_sale_order(self):
        """View the linked sale order"""
        self.ensure_one()
        if not self.sale_order_id:
            raise UserError(_('No sale order linked to this tracking.'))
        return {
            'name': _('Sale Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def get_dashboard_data(self):
        """Fetch comprehensive data for the Custom Dashboard"""
        currency_symbol = self.env.company.currency_id.symbol
        
        # 1. Summary Metrics
        all_presales = self.search([])
        total_presales = len(all_presales)
        rfq_count = len(all_presales.filtered(lambda p: p.state in ['rfq_created', 'po_confirmed', 'done']))
        done_count = len(all_presales.filtered(lambda p: p.state == 'done'))
        
        # Revenue & Margin
        # Note: Using mapped sum is fine for reasonable volumes; for millions, use read_group/SQL
        total_revenue = sum(all_presales.mapped('total_amount'))
        total_margin = sum(all_presales.mapped('line_ids').mapped('working_margin_amount'))
        avg_margin_pct = (total_margin / total_revenue * 100) if total_revenue else 0.0
        
        # Missing Products
        missing_count = sum(all_presales.mapped('missing_lines_count'))
        
        # Avg Duration (Optimized calculation)
        duration_recs = all_presales.filtered(lambda p: p.state not in ['draft', 'in_progress'])
        avg_duration = sum(duration_recs.mapped('duration_to_rfq')) / len(duration_recs) if duration_recs else 0.0

        # 2. Status Distribution
        status_data = []
        status_counts = {}
        for state, label in self._fields['state'].selection:
            count = len(all_presales.filtered(lambda p: p.state == state))
            status_counts[state] = count
            status_data.append({'label': label, 'count': count})

        # 3. Monthly Trend (Last 6 Months)
        trend_data = self.read_group(
            [('date', '>=', fields.Date.today() - timedelta(days=180))], 
            ['total_amount', 'date'], 
            ['date:month']
        )
        chart_labels = [d['date:month'] for d in trend_data]
        chart_data = [d['total_amount'] for d in trend_data]

        # 4. Tables
        # Top Customers
        top_customers = []
        customer_data = self.read_group([], ['total_amount', 'partner_id'], ['partner_id'], limit=5, orderby='total_amount desc')
        for d in customer_data:
            if d['partner_id']:
                top_customers.append({
                    'name': d['partner_id'][1],
                    'amount': d['total_amount'],
                    'formatted_amount': f"{currency_symbol} {d['total_amount']:,.2f}"
                })
        
        # Top Vendors (New)
        top_vendors = []
        # We need to sum line-level data for vendors
        vendor_data = self.env['presale.tracking.line'].read_group(
            [], ['total_amount', 'vendor_id'], ['vendor_id'], limit=5, orderby='total_amount desc'
        )
        for d in vendor_data:
            if d['vendor_id']:
                top_vendors.append({
                    'name': d['vendor_id'][1],
                    'amount': d['total_amount'],
                    'formatted_amount': f"{currency_symbol} {d['total_amount']:,.2f}"
                })

        # Recent Presales
        recent_presales = []
        recent_recs = self.search([], limit=8, order='date desc, id desc')
        for r in recent_recs:
            state_label = dict(self._fields['state'].selection).get(r.state, r.state)
            recent_presales.append({
                'id': r.id,
                'name': r.name,
                'partner': r.partner_id.name,
                'date': r.date,
                'state': state_label,
                'amount': f"{currency_symbol} {r.total_amount:,.2f}"
            })

        return {
            'summary': {
                'presales': total_presales,
                'rfqs': rfq_count,
                'done': done_count,
                'revenue': f"{currency_symbol} {total_revenue:,.2f}",
                'margin': f"{currency_symbol} {total_margin:,.2f}",
                'margin_pct': f"{avg_margin_pct:.1f}%",
                'avg_duration': f"{avg_duration:.1f} Days",
                'missing': missing_count,
            },
            'status_dist': status_data,
            'chart': {
                'labels': chart_labels,
                'datasets': [{'label': 'Revenue', 'data': chart_data}]
            },
            'tables': {
                'customers': top_customers,
                'vendors': top_vendors,
                'recent': recent_presales
            }
        }
