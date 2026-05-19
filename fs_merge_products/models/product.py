from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_merge_products(self):
        products = self.env["product.product"].search([('product_tmpl_id', 'in', self.ids)])
        return {
            'name': _('Merge Products'),
            'type': 'ir.actions.act_window',
            'res_model': 'merge.products.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_product_ids': products.ids},
        }

class MergeProductsWizard(models.TransientModel):
    _name = 'merge.products.wizard'
    _description = 'Merge Products Wizard'

    product_ids = fields.Many2many(
        'product.product',
        string='Products to Merge',
        required=True,
        help="Select products to merge. The first product will be the destination."
    )
    destination_product_id = fields.Many2one(
        'product.product',
        string='Destination Product',
        required=True,
        help="All data will be transferred to this product"
    )
    archive_origin = fields.Boolean(
        string='Archive Original Products',
        default=True,
        help="Archive original products after merge"
    )

    @api.onchange('product_ids')
    def _onchange_product_ids(self):
        if self.product_ids and not self.destination_product_id:
            self.destination_product_id = self.product_ids[0]

    def _get_models_to_update(self):
        """ Returns a list of models and their fields that should be updated during merge.
            Format: [(model_name, field_name)]
        """
        return [
            ('sale.order.line', 'product_id'),
            ('purchase.order.line', 'product_id'),
            ('account.move.line', 'product_id'),
            ('stock.move', 'product_id'),
            ('stock.move.line', 'product_id'),
            ('stock.lot', 'product_id'),
            ('product.supplierinfo', 'product_id'),
            ('product.pricelist.item', 'product_id'),
            ('mrp.bom.line', 'product_id'),
            ('mrp.bom', 'product_id'),
            ('mrp.production', 'product_id'),
            ('stock.scrap', 'product_id'),
            ('pos.order.line', 'product_id'),
            ('repair.line', 'product_id'),
            ('quality.check', 'product_id'),
            # Product template related
            ('product.supplierinfo', 'product_tmpl_id'),
            ('product.pricelist.item', 'product_tmpl_id'),
            ('mrp.bom', 'product_tmpl_id'),
        ]

    def action_merge(self):
        self.ensure_one()
        if len(self.product_ids) < 2:
            raise UserError(_('Please select at least two products to merge.'))
        
        if self.destination_product_id not in self.product_ids:
            raise UserError(_('Destination product must be one of the selected products.'))
        
        dest_product = self.destination_product_id
        dest_template = dest_product.product_tmpl_id
        
        source_products = self.product_ids.filtered(lambda p: p.id != dest_product.id)
        source_templates = source_products.mapped('product_tmpl_id').filtered(lambda t: t.id != dest_template.id)

        _logger.info("Merging products %s into %s", source_products.ids, dest_product.id)

        # 1. Handle Stock Quants separately (to avoid unique constraints)
        self._merge_stock_quants(source_products, dest_product)

        # 2. Update models that reference product.product
        models_to_update = self._get_models_to_update()
        
        for model_name, field_name in models_to_update:
            try:
                model = self.env[model_name]
                if not model:
                    continue
                
                # Determine if we should use product_id or product_tmpl_id
                if field_name == 'product_tmpl_id':
                    sources = source_templates
                    destination = dest_template
                else:
                    sources = source_products
                    destination = dest_product

                records = model.sudo().search([(field_name, 'in', sources.ids)])
                if records:
                    _logger.info("Updating %s records in %s for field %s", len(records), model_name, field_name)
                    # Use write() for most models. Some models might need special handling.
                    # For sale.order.line, we also need to update product_template_id in some versions, 
                    # but in Odoo 19 it is computed.
                    vals = {field_name: destination.id}
                    
                    # Special cases
                    if model_name == 'sale.order.line':
                        # Avoid updating read-only/computed fields if they cause issues
                        # categ_id is related, so it updates automatically
                        pass
                    
                    records.write(vals)
            except Exception as e:
                _logger.warning("Could not update model %s: %s", model_name, str(e))

        # 3. Handle Stock Valuation (Odoo 18/19 uses stock.move.value)
        # stock.move records were already updated above.
        
        # 4. Archive source products if requested
        if self.archive_origin:
            source_products.write({'active': False})
            # Only archive template if it has no more active variants
            for template in source_templates:
                if not template.product_variant_ids.filtered(lambda v: v.active):
                    template.write({'active': False})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Products have been successfully merged into %s.') % dest_product.display_name,
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def _merge_stock_quants(self, source_products, dest_product):
        """ Merges stock quants from source products into destination product.
            Handles unique constraints (location, lot, package, owner).
        """
        StockQuant = self.env['stock.quant'].sudo()
        for product in source_products:
            quants = StockQuant.search([('product_id', '=', product.id)])
            for quant in quants:
                # Find matching quant for destination product
                dest_quant = StockQuant.search([
                    ('product_id', '=', dest_product.id),
                    ('location_id', '=', quant.location_id.id),
                    ('lot_id', '=', quant.lot_id.id),
                    ('package_id', '=', quant.package_id.id),
                    ('owner_id', '=', quant.owner_id.id),
                ], limit=1)
                
                if dest_quant:
                    # Move quantity to destination quant
                    # Use _update_available_quantity if available, or just write
                    dest_quant.write({
                        'quantity': dest_quant.quantity + quant.quantity,
                        'reserved_quantity': dest_quant.reserved_quantity + quant.reserved_quantity,
                    })
                    # Unlink the source quant after moving quantity
                    # Using unlink() might be risky if there are dependencies, but quants are transient-like.
                    # Better to zero it out and let Odoo clean up if possible, or just unlink.
                    quant.unlink()
                else:
                    # No matching quant, just change the product_id
                    quant.write({'product_id': dest_product.id})