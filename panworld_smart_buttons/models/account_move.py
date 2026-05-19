from odoo import api, fields, models, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_line_count = fields.Integer(compute='_compute_invoice_line_count', string='Invoice Line Count')

    def _compute_invoice_line_count(self):
        for rec in self:
            rec.invoice_line_count = len(rec.invoice_line_ids)

    def action_view_invoice_lines(self):
        self.ensure_one()
        return {
            'name': _('Invoice Lines'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'list,form',
            'views': [(self.env.ref('panworld_smart_buttons.view_invoice_line_tree_panworld').id, 'list'), (False, 'form')],
            'domain': [('id', 'in', self.invoice_line_ids.ids)],
            'context': {
                'default_move_id': self.id,
            },
        }
