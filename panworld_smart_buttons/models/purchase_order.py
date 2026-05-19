from odoo import api, fields, models, _

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    order_line_count = fields.Integer(compute='_compute_order_line_count', string='Order Line Count')

    def _compute_order_line_count(self):
        for rec in self:
            rec.order_line_count = len(rec.order_line)

    def action_view_order_lines(self):
        self.ensure_one()
        return {
            'name': _('Order Lines'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order.line',
            'view_mode': 'list,form',
            'views': [(self.env.ref('panworld_smart_buttons.view_purchase_order_line_tree_panworld').id, 'list'), (False, 'form')],
            'domain': [('order_id', '=', self.id)],
            'context': {
                'default_order_id': self.id,
            },
        }
