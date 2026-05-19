from odoo import api, fields, models, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    move_line_count = fields.Integer(compute='_compute_move_line_count', string='Move Line Count')

    def _compute_move_line_count(self):
        for rec in self:
            rec.move_line_count = len(rec.move_ids)

    def action_view_picking_lines(self):
        self.ensure_one()
        return {
            'name': _('Picking Lines'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move',
            'view_mode': 'list,form',
            'views': [(self.env.ref('panworld_smart_buttons.view_stock_move_tree_panworld').id, 'list'), (False, 'form')],
            'domain': [('picking_id', '=', self.id)],
            'context': {
                'default_picking_id': self.id,
            },
        }
