from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class StockPickingWizard(models.TransientModel):
    _name = 'fs.stock.picking.loc.quant.update.wizard'
    _description = 'Stock Picking Wizard'

    picking_ids = fields.Many2many('stock.picking', string='Pickings')

    def action_apply(self):
        self.ensure_one()
        if not self.picking_ids:
            return {'type': 'ir.actions.act_window_close'}

        demands = {}
        for picking in self.picking_ids:
            for move in picking.move_ids:
                if not move.product_id or not move.location_id:
                    continue
                key = (move.product_id.id, move.location_id.id)
                demand = move.product_uom_qty or 0.0
                demands[key] = demands.get(key, 0.0) + demand

        _logger.info("================Aggregated Demands for Quant Update: %s", demands)

        # 2. Process each product/location group
        for (product_id, location_id), total_demand in demands.items():
            # Safety Fix: Use sudo() to ensure we see all quants regardless of user record rules
            quants = self.env['stock.quant'].sudo().search([
                ('product_id', '=', product_id),
                ('location_id', '=', location_id)
            ])
            current_on_hand = sum(quants.mapped('quantity'))

            if current_on_hand < total_demand:

                # We need to update the quant to match the demand
                _logger.info("================Product for Quant Update: %s", self.env['product.product'].browse(product_id).name)
                _logger.info("================Location for Quant Update: %s", self.env['stock.location'].browse(location_id).name)
                _logger.info("================Current On-Hand for Quant Update: %s", current_on_hand)
                _logger.info("================Total Demand for Quant Update: %s", total_demand)
                
                if quants:
                    # Update existing quant via SQL to bypass adjustment records
                    target_quant = quants[0]
                    self.env.cr.execute(
                        "UPDATE stock_quant SET quantity = %s WHERE id = %s",
                        (total_demand, target_quant.id)
                    )
                    # Set other quants for the same product/location to 0 to maintain total sum
                    if len(quants) > 1:
                        other_ids = tuple(quants[1:].ids)
                        self.env.cr.execute(
                            "UPDATE stock_quant SET quantity = 0 WHERE id IN %s",
                            (other_ids,)
                        )
                else:
                    # Create new quant if none exists
                    # Using the location's company to ensure data integrity
                    location = self.env['stock.location'].browse(location_id)
                    company_id = location.company_id.id or self.env.company.id
                    
                    self.env.cr.execute(
                        """INSERT INTO stock_quant (product_id, location_id, quantity, reserved_quantity, company_id, in_date) 
                           VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)""",
                        (product_id, location_id, total_demand, 0.0, company_id)
                    )

        # 3. Invalidate cache to reflect changes in UI
        self.env['stock.quant'].invalidate_model(['quantity'])
        
        return {'type': 'ir.actions.act_window_close'}
