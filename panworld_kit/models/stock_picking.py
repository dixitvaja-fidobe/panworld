from odoo import api, fields, models

class StockPicking(models.Model):
    _inherit = "stock.picking"

    kit_count = fields.Integer(compute='_compute_kit_count', string='Kit Count')

    @api.depends('move_ids.bom_id')
    def _compute_kit_count(self):
        for record in self:
            record.kit_count = len(record.move_ids.filtered(lambda m: m.bom_id))


