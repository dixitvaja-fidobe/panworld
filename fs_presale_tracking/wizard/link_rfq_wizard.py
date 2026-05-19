from odoo import api, fields, models, _
from markupsafe import Markup
from odoo.exceptions import UserError

class PresaleLinkRFQWizard(models.TransientModel):
    _name = 'presale.link.rfq.wizard'
    _description = 'Link Tracking Line to RFQ'

    tracking_line_ids = fields.Many2many('presale.tracking.line', string='Tracking Lines', required=True)
    vendor_id = fields.Many2one('res.partner', string='Vendor', required=True)
    sourcing_vendor_id = fields.Many2one('res.partner', string='Sourcing Vendor')
    presale_tracking_id = fields.Many2one('presale.tracking', string='Presale Tracking', readonly=True)
    company_id = fields.Many2one('res.company', related='presale_tracking_id.company_id', readonly=True)
    
    # Context fields for better UX
    line_count = fields.Integer(string='Number of Lines', compute='_compute_line_count')
    title = fields.Char(string='Title/Product', compute='_compute_title')
    
    @api.depends('tracking_line_ids')
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.tracking_line_ids)
            
    @api.depends('tracking_line_ids')
    def _compute_title(self):
        for rec in self:
            if rec.line_count == 1:
                rec.title = rec.tracking_line_ids[0].title or rec.tracking_line_ids[0].product_id.name
            else:
                rec.title = f"Multiple Products ({rec.line_count} lines)"

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        
        lines = False
        default_ids_cmd = self.env.context.get('default_tracking_line_ids')
        if default_ids_cmd and isinstance(default_ids_cmd, list) and len(default_ids_cmd) > 0:
            if default_ids_cmd[0][0] == 6:
                line_ids = default_ids_cmd[0][2]
                lines = self.env['presale.tracking.line'].browse(line_ids)
                
        if not lines:
            active_ids = self.env.context.get('active_ids', [])
            if active_ids and self.env.context.get('active_model') == 'presale.tracking.line':
                lines = self.env['presale.tracking.line'].browse(active_ids)
                
        if lines:
            
            # Validation 1: Must belong to same presale tracking (just in case)
            if len(lines.mapped('tracking_id')) > 1:
                raise UserError(_("Please select lines from the same Presale Tracking."))
                
            # Validation 2: Must not be already linked to a CONFIRMED RFQ
            for line in lines:
                if line.is_linked_to_po:
                    # Check if any linked PO is NOT in draft
                    non_draft_pos = line.purchase_order_line_ids.filtered(lambda l: l.order_id.state != 'draft')
                    if non_draft_pos:
                        raise UserError(_("One or more selected lines are already linked to a confirmed RFQ. Please only select unlinked lines or lines linked to draft RFQs."))
                
            # Validation 3: Must share the same vendor
            vendors = lines.mapped('vendor_id')
            if len(vendors) == 0 or not vendors[0]:
                raise UserError(_("Please ensure a Vendor is selected on all lines before linking."))
            if len(vendors) > 1:
                raise UserError(_("You can only link multiple lines at once if they all have the exact same Vendor."))
            
            # Validation 4: Must share the same sourcing vendor
            sourcing_vendors = lines.mapped('sourcing_vendor_id')
            if len(sourcing_vendors.ids) > 1:
                 raise UserError(_("You can only link multiple lines at once if they all have the exact same Sourcing Vendor."))
                
            res['tracking_line_ids'] = [(6, 0, lines.ids)]
            res['vendor_id'] = vendors[0].id
            res['sourcing_vendor_id'] = sourcing_vendors[0].id if sourcing_vendors else False
            res['presale_tracking_id'] = lines[0].tracking_id.id
            
        return res
    vendor_name = fields.Char(related='vendor_id.name', string='Vendor Name', readonly=True)
    
    selection_type = fields.Selection([
        ('existing', 'Link to Existing RFQ'),
        ('new', 'Create New RFQ')
    ], string='Selection Type', default='existing', required=True)

    target_po_id = fields.Many2one(
        'purchase.order', 
        string='Target RFQ', 
        domain="[('state', '=', 'draft'), ('company_id', '=', company_id), ('sourcing_vendor_id', '=', sourcing_vendor_id)]"
    )

    def action_confirm_link(self):
        self.ensure_one()
        if not self.tracking_line_ids:
            return {'type': 'ir.actions.act_window_close'}
            
        # Validation: Ensure no lines are linked to CONFIRMED RFQs
        for line in self.tracking_line_ids:
            if line.is_linked_to_po:
                non_draft_pos = line.purchase_order_line_ids.filtered(lambda l: l.order_id.state != 'draft')
                if non_draft_pos:
                    raise UserError(_("One or more lines are already linked to a confirmed RFQ."))

        # Remove existing draft links if any (break old connections)
        existing_pol = self.tracking_line_ids.mapped('purchase_order_line_ids').filtered(lambda l: l.order_id.state == 'draft')
        if existing_pol:
            existing_pol.with_context(bypass_presale_track_block=True).unlink()
            
        target_po = self.target_po_id
        
        if self.selection_type == 'new':
            # Determine best currency from sourcing vendor or standard vendor
            target_vendor = self.sourcing_vendor_id or self.vendor_id
            # We can use the logic from the tracking line if we have it, 
            # but here we just grab the best match.
            currency = target_vendor.sudo().property_purchase_currency_id or target_vendor.sudo().currency_id
            
            # Create a brand new PO for this vendor
            target_po = self.env['purchase.order'].create({
                'partner_id': self.vendor_id.id,
                'sourcing_vendor_id': self.sourcing_vendor_id.id if self.sourcing_vendor_id else False,
                'currency_id': currency.id if currency else self.company_id.currency_id.id,
                'presale_tracking_id': self.presale_tracking_id.id,
                'date_order': fields.Datetime.now(),
                'origin': self.presale_tracking_id.name,
            })
            target_po.message_post(body=_("Created from the Presale tracker %s") % self.presale_tracking_id.name)
        elif not target_po:
            raise UserError(_("Please select a target RFQ or choose 'Create New RFQ'."))

        # If linking to an existing RFQ for a different vendor, update the tracking lines vendor
        if self.selection_type == 'existing' and target_po and target_po.partner_id != self.vendor_id:
             self.tracking_line_ids.with_context(presale_sync_from_po=True).write({
                 'vendor_id': target_po.partner_id.id,
             })

        pol_vals = []
        for line in self.tracking_line_ids:
            pol_vals.append({
                'order_id': target_po.id,
                'product_id': line.product_id.id,
                'name': line.product_id.name or line.title,
                'product_qty': line.qty,
                'product_uom_id': line.product_id.uom_id.id,
                'price_unit': line.list_price,
                'price_unit_no_markup': line.list_price,
                'po_list_price': line.list_price,
                'po_list_price_no_markup': line.list_price,
                'po_discount': line.pub_disc,
                'discount': line.pub_disc,
                'date_planned': fields.Date.today(),
                'presale_tracking_line_id': line.id,
                'rfq_qty': line.qty,
                'po_qty': line.qty,
                'related_so': self.presale_tracking_id.sale_order_id.id,
            })
            
        # Apply sourcing markup to each line dict if the PO has a markup
        markup_percent = target_po.sourcing_markup if target_po.sourcing_markup > 0 else (15.0 if self.sourcing_vendor_id else 0.0)
        if markup_percent > 0:
            markup_factor = 1 + (markup_percent / 100.0)
            for vals in pol_vals:
                # Use the stored no‑markup values as base
                base_price = vals.get('price_unit_no_markup', vals['price_unit'])
                vals['price_unit'] = base_price * markup_factor
                base_list = vals.get('po_list_price_no_markup', vals['po_list_price'])
                vals['po_list_price'] = base_list * markup_factor

        if pol_vals:
            self.env['purchase.order.line'].with_context(bypass_presale_track_block=True).create(pol_vals)
            
            # Post log note on the Presale Tracking record
            linked_line_names = []
            for line in self.tracking_line_ids:
                name = line.product_id.name or line.title or line.isbn or _('Unnamed Line')
                linked_line_names.append(name)
            
            lines_summary = ", ".join(linked_line_names[:5])
            if len(linked_line_names) > 5:
                lines_summary += _("... (%d lines total)") % len(linked_line_names)
                
            po_link = Markup("<a href='#' data-oe-model='purchase.order' data-oe-id='{}'>{}</a>").format(target_po.id, target_po.name)
            note_msg = Markup(_("Line(s) [{}] linked to {} for Vendor {}")).format(
                lines_summary, po_link, target_po.partner_id.name
            )
            self.presale_tracking_id.message_post(body=note_msg)
            
        return {'type': 'ir.actions.client', 'tag': 'reload'}
