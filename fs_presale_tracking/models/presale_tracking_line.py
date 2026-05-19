from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from markupsafe import Markup


class PresaleTrackingLine(models.Model):
    _name = 'presale.tracking.line'
    _description = 'Presale Tracking Line'
    _order = 'sequence, id'

    tracking_id = fields.Many2one(
        'presale.tracking',
        string='Tracking',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(string='Sequence', default=10)
    
    state = fields.Selection(
        related='tracking_id.state',
        string='Status',
        readonly=True,
    )

    # Basic Info (from CSV import)
    isbn = fields.Char(string='ISBN', required=True)
    title = fields.Char(string='Title')
    qty = fields.Integer(string='Qty', default=1)

    @api.constrains('qty')
    def _check_qty(self):
        for record in self:
            if record.qty <= 0:
                raise UserError(_("Quantity must be a positive integer."))
    
    # Product Link (for Sale Order creation)
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        help="Link to product for creating sale order lines"
    )
    
    # Additional Product Info
    subject_id = fields.Char(
        string='Subject',
        related='product_id.subject',
    )
    grade_id = fields.Many2one(
        'product.grade',
        string='Grade',
        related='product_id.product_tmpl_id.uk_wholesaler_id',
    )
    author_id = fields.Many2one(
        'res.partner',
        string='Author',
        related='product_id.author_id',
    )
    publisher_id = fields.Many2one(
        'res.partner',
        string='Publisher',
        related='product_id.publisher_id',
    )
    alt_isbn = fields.Char(string='Alt ISBN')
    format_id = fields.Many2one(
        'product.subtitle',
        string='Format',
        related='product_id.product_tmpl_id.subtitle',
    )
    classification_id = fields.Many2one(
        'product.classification',
        string='Classification',
        related='product_id.product_tmpl_id.non_uk_wholesaler_id',
    )
    remarks = fields.Selection([
        ('active', 'Active'),
        ('reprint', 'Reprint'),
        ('os', 'OS - Out of Stock'),
        ('tos', 'TOS - Temp Out of Stock'),
        ('oop', 'OOP - Out of Print'),
        ('mr', 'MR - Market Restricted'),
        ('nyp', 'NYP - Not yet Published'),
        ('in_stock', 'In Stock'),
        ('foc', 'FOC - Free of Cost'),
        ('pod', 'POD - Print on Demand'),
        ('unable', 'Unable to Supply'),
    ], string='Remarks')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.title = self.product_id.name
        else:
            self.title = False

    @api.depends('product_id')
    def _compute_seller_id(self):
        # Fetch all company partners to exclude (branches/internal companies)
        company_partners = self.env['res.company'].sudo().search([]).mapped('partner_id')
        seller_cache = {}
        for line in self:
            if not line.product_id:
                line.seller_id = False
                continue
            
            product_id = line.product_id.id
            if product_id in seller_cache:
                line.seller_id = seller_cache[product_id]
                continue

            # Use search().sudo() to bypass company visibility rules on seller_ids relation
            sellers = self.env['product.supplierinfo'].sudo().search([
                ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
                ('partner_id', 'not in', company_partners.ids)
            ])
            
            if sellers:
                # Optimize: Use in-memory sorting
                sorted_sellers = sellers.sorted(
                    key=lambda s: (s.date_start or fields.Date.to_date('1900-01-01'), s.id), 
                    reverse=True
                )
                latest_seller = sorted_sellers[0]
                seller_cache[product_id] = latest_seller
                line.seller_id = latest_seller
            else:
                seller_cache[product_id] = False
                line.seller_id = False

    @api.depends('seller_id')
    def _compute_vendor_id(self):
        for line in self:
            if line.seller_id:
                line.vendor_id = line.seller_id.partner_id

    @api.onchange('seller_id')
    def _onchange_seller_id_sync(self):
        if self.seller_id:
            self.vendor_id = self.seller_id.partner_id
            self.vendor_currency_id = self.seller_id.currency_id

    def _get_best_vendor_currency(self, vendor):
        """ Standardizes currency fetching logic with a country-based fallback. """
        self.ensure_one()
        vendor = vendor.sudo()
        # 1. Specific Purchase Currency (e.g., Partner set to USD explicitly)
        if vendor.property_purchase_currency_id:
            return vendor.property_purchase_currency_id
        # 2. Country Fallback (Pick currency based on address)
        if vendor.country_id and vendor.country_id.currency_id:
            return vendor.country_id.currency_id
        # 3. Final Fallback: Company Currency
        return self.tracking_id.company_id.currency_id

    @api.depends('seller_id', 'vendor_id', 'sourcing_vendor_id')
    def _compute_vendor_currency_id(self):
        for line in self:
            if line.sourcing_vendor_id:
                # 1. Absolute priority: Sourcing vendor's currency
                line.vendor_currency_id = line._get_best_vendor_currency(line.sourcing_vendor_id)
            elif line.vendor_id:
                # 2. Second priority: Standard Vendor's currency
                line.vendor_currency_id = line._get_best_vendor_currency(line.vendor_id)
            elif line.seller_id:
                # 3. Third priority: Pricelist/Seller currency
                line.vendor_currency_id = line.seller_id.currency_id
            else:
                line.vendor_currency_id = line.tracking_id.company_id.currency_id

    @api.constrains('sourcing_vendor_id')
    def _check_sourcing_vendor_po_link(self):
        for line in self:
            # Check all linked Purchase Order lines
            for po_line in line.purchase_order_line_ids:
                order = po_line.order_id
                # If the PO has a sourcing vendor, the line MUST match it
                if order.sourcing_vendor_id and line.sourcing_vendor_id != order.sourcing_vendor_id:
                    raise ValidationError(_(
                        "This line is linked to RFQ '%s' which is restricted to Sourcing Vendor: %s. "
                        "You cannot change or clear the Sourcing Vendor on this line while it is linked."
                    ) % (order.name, order.sourcing_vendor_id.display_name))
    
    @api.depends('seller_id')
    def _compute_price_details(self):
        # Skip recompute if we are specifically syncing from PO/SO to keep manual overrides
        if self.env.context.get('presale_sync_from_po') or self.env.context.get('presale_sync_from_so'):
            return
            
        for line in self:
            if line.seller_id:
                line.list_price = line.seller_id.price
                line.pub_disc = getattr(line.seller_id, 'discount', 0.0)

    @api.onchange('vendor_id')
    def _onchange_vendor_id_sync(self):
        if self.vendor_id and not self.seller_id:
             # Use the same logic as compute for sync
             self._compute_vendor_currency_id()

    @api.depends('product_id')
    def _compute_available_seller_ids(self):
        # Cache company partners to avoid redundant searches
        company_partners = self.env['res.company'].sudo().search([]).mapped('partner_id')
        for line in self:
            if not line.product_id:
                line.available_seller_ids = False
                continue
            # Use direct search().sudo() to bypass company visibility rules
            line.available_seller_ids = self.env['product.supplierinfo'].sudo().search([
                ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
                ('partner_id', 'not in', company_partners.ids)
            ])

    available_seller_ids = fields.Many2many(
        'product.supplierinfo',
        compute='_compute_available_seller_ids',
        string='Available Sellers'
    )

    # Vendor Pricing
    seller_id = fields.Many2one(
        'product.supplierinfo',
        string='Available Pricelists',
        compute='_compute_seller_id',
        store=True,
        readonly=False,
        tracking=True,
        domain="[('id', 'in', available_seller_ids)]"
    )
    product_tmpl_id = fields.Many2one(
        'product.template', 
        related='product_id.product_tmpl_id', 
        string='Product Template'
    )

    vendor_id = fields.Many2one(
        'res.partner',
        string='Vendor',
        domain=[('supplier_rank', '>', 0)],
        compute='_compute_vendor_id',
        store=True,
        readonly=False,
    )
    sourcing_vendor_id = fields.Many2one(
        'res.partner',
        string='Sourcing Vendor',
        domain=[('supplier_rank', '>', 0)],
    )
    vendor_currency_id = fields.Many2one(
        'res.currency',
        string='Vendor Currency',
        compute='_compute_vendor_currency_id',
        store=True,
        readonly=False,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='tracking_id.currency_id',
        readonly=True,
    )
    customer_currency_id = fields.Many2one(
        'res.currency',
        string='Customer Currency',
        related='tracking_id.customer_currency_id',
        store=True,
    )

    purchase_order_line_ids = fields.One2many(
        'purchase.order.line',
        'presale_tracking_line_id',
        string='Purchase Order Lines'
    )
    sale_order_line_ids = fields.One2many(
        'sale.order.line',
        'presale_tracking_line_id',
        string='Sale Order Lines'
    )
    is_linked_to_po = fields.Boolean(
        string='Linked to RFQ',
        compute='_compute_link_status',
        store=True,
    )
    is_linked_to_so = fields.Boolean(
        string='Linked to SO',
        compute='_compute_link_status',
        store=True,
    )
    is_fully_linked = fields.Boolean(
        string='Fully Linked',
        compute='_compute_link_status',
        store=True,
    )
    is_so_up_to_date = fields.Boolean(
        string='SO Sync Up to Date',
        default=True,
        help="If false, this line has changes not yet reflected in the Sale Order",
    )

    linked_po_id = fields.Many2one(
        'purchase.order',
        compute='_compute_linked_po_id',
        string='Linked RFQ'
    )
    


    @api.depends('purchase_order_line_ids', 'purchase_order_line_ids.order_id')
    def _compute_linked_po_id(self):
        for line in self:
            po_lines = line.purchase_order_line_ids
            if po_lines:
                # Get the first unique purchase order
                line.linked_po_id = po_lines.mapped('order_id')[:1]
            else:
                line.linked_po_id = False

    @api.depends('purchase_order_line_ids', 'tracking_id.sale_order_id', 'product_id', 'tracking_id.sale_order_id.order_line.presale_tracking_line_id')
    def _compute_link_status(self):
        for line in self:
            line.is_linked_to_po = len(line.purchase_order_line_ids) > 0
            
            # Strict 1:1 check: does an SO line exist that links back to THIS specific line?
            so = line.tracking_id.sale_order_id
            if so:
                # Check if any SOL in this SO matches this line's ID
                line.is_linked_to_so = line.id in so.order_line.mapped('presale_tracking_line_id.id')
            else:
                line.is_linked_to_so = False
            line.is_fully_linked = line.is_linked_to_po and line.is_linked_to_so


    unit_price = fields.Monetary(
        string='Unit Price',
        currency_field='customer_currency_id', 
        compute='_compute_unit_price',
        inverse='_inverse_unit_price',
        store=True,
        readonly=True,
    )

    @api.depends('list_price', 'conv_rate', 'disc_percent', 'customer_currency_id', 'vendor_currency_id', 'currency_id')
    def _compute_unit_price(self):
        for line in self:
            discount_factor = 1.0 - (line.disc_percent or 0.0) / 100.0
            price_vendor = line.list_price * discount_factor
            
            # 1. Direct Case: Vendor and Customer use same currency
            if line.vendor_currency_id and line.customer_currency_id and line.vendor_currency_id == line.customer_currency_id:
                line.unit_price = round(price_vendor, 1)
                continue

            # 2. Case: Manual / Consistent Conversion
            if line.conv_rate and line.customer_currency_id != line.vendor_currency_id:
                # Use the manual rate for the quoted price regardless of currency symbol
                line.unit_price = round(price_vendor * line.conv_rate, 1)
                continue

            # 3. Fallback: Convert Case: Use Odoo's _convert
            if line.vendor_currency_id and line.customer_currency_id:
                line.unit_price = round(line.vendor_currency_id._convert(
                    price_vendor,
                    line.customer_currency_id,
                    line.tracking_id.company_id,
                    line.tracking_id.date or fields.Date.today()
                ), 1)
            else:
                # Fallback
                line.unit_price = round(line.list_price_base * discount_factor, 1)

    def _inverse_unit_price(self):
        """Calculate discount back from price when price is modified"""
        for line in self:
            if not line.list_price:
                continue
            
            # 1. Direct Case: Vendor and Customer use same currency
            if line.vendor_currency_id and line.customer_currency_id and line.vendor_currency_id == line.customer_currency_id:
                unit_price_vendor = line.unit_price
            
            # 2. Case: Manual Conv. Rate (Tracking Currency is AED)
            elif line.customer_currency_id and line.currency_id and line.customer_currency_id == line.currency_id:
                if line.conv_rate:
                    unit_price_vendor = line.unit_price / line.conv_rate
                else:
                    unit_price_vendor = line.unit_price
            
            # 3. Convert Case: Direct conversion Customer -> Vendor (one step)
            elif line.vendor_currency_id and line.customer_currency_id:
                unit_price_vendor = line.customer_currency_id._convert(
                    line.unit_price,
                    line.vendor_currency_id,
                    line.tracking_id.company_id,
                    line.tracking_id.date or fields.Date.today()
                )
            else:
                unit_price_vendor = line.unit_price # Fallback

            # Calculate new discount percent against Vendor List Price
            if line.list_price:
                new_disc = (1.0 - (unit_price_vendor / line.list_price)) * 100.0
                line.disc_percent = round(new_disc, 2)

    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_total_amount',
        digits='Product Price',
        store=True,
    )
    
    # Exchange Rate & USD
    exchange_rate = fields.Float(string='Exchange Rate', digits=(12, 6), default=1.0)
    total_usd = fields.Float(
        string='Total USD',
        compute='_compute_total_usd',
        store=True,
        digits='Product Price',
    )
    
    # Pricing Details
    list_price = fields.Monetary(
        string='LP (List Price)', 
        currency_field='vendor_currency_id',
        compute='_compute_price_details',
        readonly=False,
        store=True,
    )

    @api.constrains('list_price')
    def _check_list_price(self):
        for record in self:
            if record.list_price < 0:
                raise UserError(_("List price cannot be negative."))
    gross_lp = fields.Monetary(
        string='Gross LP', 
        currency_field='vendor_currency_id',
        compute='_compute_gross_lp',
        store=True,
    )
    conv_rate = fields.Float(
        string='Conv. Rate', 
        digits=(12, 3),
        compute='_compute_conv_rate',
        readonly=False,
        store=True,
    )
    list_price_base = fields.Monetary(
        string='List Price in Currency',
        currency_field='currency_id',
        compute='_compute_list_price_base',
        store=True,
    )
    
    # Discounts
    disc_percent = fields.Float(string='Sales Disc %', digits=(5, 2))
    pub_disc = fields.Float(
        string='Purchase Disc %', 
        digits=(5, 2),
        compute='_compute_price_details',
        store=True,
        readonly=False,
    )
    
    # Working Margin
    working_margin = fields.Float(
        string='Working Margin',
        compute='_compute_working_margin',
        digits='Product Price',
        store=True,
    )
    working_margin_percent = fields.Float(
        string='WM %',
        compute='_compute_working_margin',
        digits=(5, 2),
        store=True,
    )
    working_margin_amount = fields.Float(
        string='WM $',
        compute='_compute_working_margin',
        digits='Product Price',
        store=True,
    )
    
    # Other Info
    program = fields.Char(string='Program')
    stock_availability = fields.Selection([
        ('in_stock', 'In Stock'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('on_order', 'On Order'),
        ('pubsey', 'Pubsey'),
    ], string='Stock Availability')

    @api.depends('qty', 'unit_price')
    def _compute_total_amount(self):
        for line in self:
            line.total_amount = round(line.qty * line.unit_price, 1)

    @api.depends('total_amount', 'exchange_rate')
    def _compute_total_usd(self):
        for line in self:
            if line.exchange_rate:
                line.total_usd = round(line.total_amount / line.exchange_rate, 1)
            else:
                line.total_usd = round(line.total_amount, 1)

    @api.depends('list_price', 'qty')
    def _compute_gross_lp(self):
        for line in self:
            line.gross_lp = round(line.list_price * line.qty, 1)

    @api.depends('vendor_currency_id', 'currency_id', 'tracking_id.company_id', 'tracking_id.date')
    def _compute_conv_rate(self):
        for line in self:
            line.conv_rate = 1.0
            if line.vendor_currency_id and line.currency_id and line.vendor_currency_id != line.currency_id:
                # Use Odoo's standard conversion rate logic which is truly universal
                # It calculates the rate from vendor_currency to tracking_currency (currency_id)
                rate = line.vendor_currency_id._get_conversion_rate(
                    line.vendor_currency_id,
                    line.currency_id,
                    line.tracking_id.company_id or self.env.company,
                    line.tracking_id.date or fields.Date.context_today(line)
                )
                line.conv_rate = rate

    @api.depends('list_price', 'conv_rate')
    def _compute_list_price_base(self):
        for line in self:
            line.list_price_base = round(line.list_price * line.conv_rate, 1)

    @api.depends('list_price_base', 'unit_price', 'qty')
    def _compute_working_margin(self):
        for line in self:
            revenue = line.list_price_base
            cost = line.unit_price
            
            if revenue:
                line.working_margin = round(revenue - cost, 1)
                line.working_margin_percent = round(((revenue - cost) / revenue) * 100, 2)
                line.working_margin_amount = round((revenue - cost) * line.qty, 1)
            else:
                line.working_margin = 0.0
                line.working_margin_percent = 0.0
                line.working_margin_amount = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'is_so_up_to_date' not in vals:
                vals['is_so_up_to_date'] = False
        records = super().create(vals_list)
        
        # Performance: Pre-fetch trackings and check states
        trackings = records.mapped('tracking_id').filtered(
            lambda t: t.state in ['rfq_created', 'po_confirmed', 'done']
        )
        if not trackings:
            return records

        # Pre-fetch existing RFQs for these trackings to avoid N+1 queries
        existing_rfqs = self.env['purchase.order'].search([
            ('presale_tracking_id', 'in', trackings.ids),
            ('state', '=', 'draft')
        ])
        # Group RFQs by (presale_tracking_id, partner_id)
        rfq_map = {}
        for rfq in existing_rfqs:
            key = (rfq.presale_tracking_id.id, rfq.partner_id.id)
            if key not in rfq_map:
                rfq_map[key] = []
            rfq_map[key].append(rfq)

        sol_vals_list = []
        pol_vals_list = []

        sol_fields = self.env['sale.order.line']._fields
        for record in records:
            tracking = record.tracking_id
            if tracking not in trackings:
                continue

        # Sync into Sale Order (Aggregated by Product)
        trackings_with_so = trackings.filtered(lambda t: t.sale_order_id)
        if trackings_with_so:
            for tracking in trackings_with_so:
                # Only sync if there's at least one line with a product (to avoid unnecessary validation errors)
                if any(r.product_id for r in records if r.tracking_id == tracking):
                    tracking.with_context(bypass_presale_track_block=True, skip_validation=True).action_sync_sale_order_lines()
            if record.vendor_id and record.product_id:
                key = (tracking.id, record.vendor_id.id)
                pos = rfq_map.get(key, [])
                if len(pos) == 1:
                    po = pos[0]
                    pol_vals_list.append({
                        'order_id': po.id,
                        'product_id': record.product_id.id,
                        'name': record.product_id.name or record.title,
                        'product_qty': record.qty,
                        'product_uom_id': record.product_id.uom_id.id,
                        'po_list_price': record.list_price,
                        'po_discount': record.pub_disc,
                        'discount': record.pub_disc,
                        'date_planned': fields.Date.today(),
                        'presale_tracking_line_id': record.id,
                        'rfq_qty': record.qty,
                        'po_qty': record.qty,
                    })

        if sol_vals_list:
            self.env['sale.order.line'].with_context(bypass_presale_track_block=True).create(sol_vals_list)
        if pol_vals_list:
            self.env['purchase.order.line'].with_context(bypass_presale_track_block=True).create(pol_vals_list)
            
        return records



    def write(self, vals):
        # Validation: Prevent changing vendor or product if already linked to a PO
        # BUT allow if the change is coming from the RFQ sync (presale_sync_from_po)
        if not self.env.context.get('presale_sync_from_po'):
            if 'vendor_id' in vals or 'product_id' in vals or 'seller_id' in vals or 'vendor_currency_id' in vals:
                for record in self:
                    if record.is_linked_to_po:
                        raise UserError(_("You cannot change the Vendor or Product on a line that is already linked to an RFQ. Please unlink the line first if you need to make changes."))
        

        # Reset SO sync flag if relevant fields change
        sync_so_fields = ['qty', 'unit_price', 'product_id', 'list_price', 'pub_disc', 'disc_percent', 'list_price_base', 'title', 'suffix', 'description', 'conv_rate']
        if any(f in vals for f in sync_so_fields):
            vals['is_so_up_to_date'] = False

        res = super().write(vals)
        self._sync_to_orders(vals)
        return res

    def _sync_to_orders(self, vals):
        """Batch synchronize changes to linked Purchase and Sale order lines"""
        # Fields that trigger a PO update
        sync_po_fields = ['qty', 'list_price', 'pub_disc', 'product_id', 'vendor_id']
        # Fields that trigger an SO update (including fields that affect computed unit_price)
        sync_so_fields = ['qty', 'unit_price', 'product_id', 'list_price', 'pub_disc', 'disc_percent', 'list_price_base', 'suffix', 'description', 'conv_rate']
        
        ctx = self.env.context
        from_po = ctx.get('presale_sync_from_po')
        from_so = ctx.get('presale_sync_from_so')

        if not any(f in vals for f in sync_po_fields + sync_so_fields):
            return

        # Single combined search for efficiency
        po_lines = self.env['purchase.order.line']
        so_lines = self.env['sale.order.line']
        
        # Don't search for PO lines if we just came from PO, unless we specifically need to update OTHER POs (unlikely in this model)
        if not from_po:
            po_lines = self.env['purchase.order.line'].search([('presale_tracking_line_id', 'in', self.ids)])
        
        # Don't search for SO lines if we just came from SO
        if not from_so:
            so_lines = self.env['sale.order.line'].search([('presale_tracking_line_id', 'in', self.ids)])

        if not po_lines and not so_lines:
            return

        # Map by record id for efficient access
        po_line_map = {}
        for pol in po_lines:
            po_line_map.setdefault(pol.presale_tracking_line_id.id, self.env['purchase.order.line'])
            po_line_map[pol.presale_tracking_line_id.id] += pol

        so_line_map = {}
        for sol in so_lines:
            so_line_map.setdefault(sol.presale_tracking_line_id.id, self.env['sale.order.line'])
            so_line_map[sol.presale_tracking_line_id.id] += sol

        for record in self:
            # Current values, prioritizing vals (the new ones being saved)
            qty = vals.get('qty', record.qty)
            list_price = vals.get('list_price', record.list_price)
            pub_disc = vals.get('pub_disc', record.pub_disc)
            disc_percent = vals.get('disc_percent', record.disc_percent)
            unit_price = vals.get('unit_price', record.unit_price)

            # 1. Update PO Lines (unless update originated from a PO)
            if not from_po:
                matching_pol = po_line_map.get(record.id)
                if matching_pol:
                    for po_line in matching_pol:
                        if po_line.order_id.state != 'draft' and any(f in vals for f in ['product_id', 'vendor_id']):
                            continue
                            
                        po_vals = {}
                        if 'qty' in vals:
                            po_vals.update({'rfq_qty': qty, 'product_qty': qty})
                        if 'list_price' in vals:
                            po_vals['po_list_price'] = list_price
                        if 'pub_disc' in vals:
                            # Sync both fields to PO line
                            po_vals.update({'po_discount': pub_disc, 'discount': pub_disc})
                        if 'product_id' in vals:
                            prod_id = vals.get('product_id')
                            product = self.env['product.product'].browse(prod_id)
                            po_vals.update({
                                'product_id': prod_id,
                                'product_uom_id': product.uom_id.id
                            })
                        
                        if 'vendor_id' in vals and po_line.order_id.state == 'draft':
                            v_id = vals.get('vendor_id')
                            new_po = self.env['purchase.order'].search([
                                ('presale_tracking_id', '=', record.tracking_id.id),
                                ('partner_id', '=', v_id),
                                ('state', '=', 'draft')
                            ], limit=1)
                            if new_po:
                                po_vals['order_id'] = new_po.id
                                
                        if po_vals:
                            po_line.with_context(presale_sync_from_po=True).write(po_vals)

            # 2. Update SO Lines (unless update originated from an SO)
            if not from_so:
                tracking = record.tracking_id
                if tracking.sale_order_id and (record.product_id or'product_id' in vals):
                    # Find the SO line for THIS specific tracking line
                    so_line = self.env['sale.order.line'].search([
                        ('order_id', '=', tracking.sale_order_id.id),
                        ('presale_tracking_line_id', '=', record.id)
                    ], limit=1)
                    
                    if so_line:
                        so_vals = {}
                        if 'qty' in vals:
                            so_vals.update({'product_uom_qty': qty, 'so_qty': qty, 'so_quantity': qty})
                        if any(f in vals for f in ['unit_price', 'list_price', 'pub_disc', 'disc_percent', 'list_price_base', 'conv_rate']):
                            so_vals['price_unit'] = unit_price
                            if 'list_price' in so_line._fields:
                                so_vals['list_price'] = unit_price
                        
                        if so_vals:
                            so_line.with_context(bypass_presale_track_block=True, presale_sync_from_so=True).write(so_vals)
                        record.is_so_up_to_date = True
                    else:
                        # Fallback to main sync to handle creation/re-link
                        tracking.with_context(bypass_presale_track_block=True, skip_validation=True).action_sync_sale_order_lines()

    def action_delete_line(self):
        """Action trigger for delete button with confirmation"""
        return self.unlink()

    def unlink(self):
        # Collect affected trackings to sync after unlink
        trackings_to_sync = self.mapped('tracking_id').filtered(lambda t: t.sale_order_id)
        
        for record in self:
            # Check for confirmed/locked/done orders before allowing deletion
            if any(l.order_id.state not in ['draft', 'sent', 'cancel'] for l in record.purchase_order_line_ids):
                raise UserError(_("Cannot delete a line linked to a confirmed Purchase Order."))
            
            if any(l.order_id.state not in ['draft', 'sent', 'cancel'] for l in record.sale_order_line_ids):
                raise UserError(_("Cannot delete a line linked to a confirmed Sale Order."))

            # Prepare message for chatter
            product_name = record.product_id.display_name or record.title or record.isbn
            msg = Markup(_("🗑️ Deleted Tracking Line: {} (ISBN: {}, Qty: {})")).format(
                product_name, record.isbn or 'N/A', record.qty
            )
            
            # Post to Presale Tracking
            if record.tracking_id:
                record.tracking_id.message_post(body=msg)
                
            # Post to linked Sale Order
            if record.tracking_id.sale_order_id:
                record.tracking_id.sale_order_id.message_post(body=msg)

            # Delete linked RFQ lines only if the orders are still in draft/sent
            po_lines = self.env['purchase.order.line'].search([('presale_tracking_line_id', '=', record.id)])
            valid_po_lines = po_lines.filtered(lambda l: l.order_id.state in ['draft', 'sent'])
            
            # Post to related Purchase Orders before unlinking lines
            for po in valid_po_lines.mapped('order_id'):
                po.message_post(body=msg)
                
            valid_po_lines.with_context(bypass_presale_track_block=True).unlink()
            
        res = super().unlink()
        
        # Sync SO lines to update aggregated quantities
        for tracking in trackings_to_sync:
            if tracking.exists():
                tracking.with_context(bypass_presale_track_block=True).action_sync_sale_order_lines()
                
        return res


