from odoo import api, fields, models, _
from odoo.exceptions import UserError
from markupsafe import Markup

class SaleOrderCreateRFQWizard(models.TransientModel):
    _name = 'sale.order.create.rfq.wizard'
    _description = 'Create RFQ from Sale Order'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    vendor_id = fields.Many2one('res.partner', string='Select Vendor', required=True, domain="[('supplier_rank', '>', 0)]")
    
    def action_create_rfq(self):
        self.ensure_one()
        order = self.sale_order_id
        vendor = self.vendor_id
        
        if not order.order_line:
            raise UserError(_("The Sale Order has no lines."))
            
        if order.rfq_exists:
            raise UserError(_("A Purchase Quotation has already been created for this order."))

        po_vals = {
            'partner_id': vendor.id,
            'currency_id': order.currency_id.id,
            'company_id': order.company_id.id,
            'origin': order.name,
            'order_line': [],
        }
        
        for line in order.order_line:
            if line.display_type or not line.product_id:
                continue
            
            # Option C: Use the Selling Price from the Sale Order as the Purchase Price
            price_unit = line.price_unit

            # Try to get discounts from the linked presale tracking line
            tracking_line = line.intercompany_presale_tracking_line_id or line.presale_tracking_line_id
            po_discount = tracking_line.pub_disc if tracking_line else 0.0

            po_line_vals = {
                'product_id': line.product_id.id,
                'name': line.product_id.display_name,
                'product_qty': line.product_uom_qty,
                'rfq_qty': line.product_uom_qty,   # Add rfq_qty matching the SO quantity
                'po_qty': line.product_uom_qty,    # Add po_qty matching the SO quantity
                'product_uom_id': line.product_uom_id.id,
                'price_unit': tracking_line.list_price,
                'po_list_price': tracking_line.list_price,
                'date_planned': fields.Datetime.now(),
                'related_so': order.id,
                'po_discount': po_discount,
                'discount': po_discount,
            }
            
            po_vals['order_line'].append((0, 0, po_line_vals))

        if not po_vals['order_line']:
            raise UserError(_("No valid lines found to create RFQ."))

        po = self.env['purchase.order'].with_context(bypass_presale_track_block=True).create(po_vals)
        
        # Log on Purchase Order
        po_msg = _("This RFQ was generated from Inter-company Sale Order: %s") % order._get_html_link()
        po.message_post(body=Markup(po_msg))
        
        # Log on Sale Order
        so_msg = _("Purchase Quotation %s has been generated for this order.") % po._get_html_link()
        order.message_post(body=Markup(so_msg))
            
        return {
            'name': _('Generated RFQ'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': po.id,
            'target': 'current',
        }
