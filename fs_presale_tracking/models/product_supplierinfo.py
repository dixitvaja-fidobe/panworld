from odoo import models, fields, api

class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    discount = fields.Float(string='Discount', digits='Discount', default=0.0)

    @api.depends('partner_id', 'price', 'currency_id', 'create_date', 'discount')
    @api.depends_context('presale_tracking_view')
    def _compute_display_name(self):
        super()._compute_display_name()
        if self.env.context.get('presale_tracking_view'):
            for reg in self:
                date_val = reg.create_date.date() if reg.create_date else fields.Date.today()
                discount_str = f" | Disc: {reg.discount}%" if reg.discount else ""
                reg.display_name = f"{reg.partner_id.name} | {reg.price} {reg.currency_id.symbol}{discount_str} | {date_val}"
