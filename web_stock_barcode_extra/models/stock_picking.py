# -*- coding: utf-8 -*-

from odoo import models, api, fields

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _get_stock_barcode_data(self):
        data = super(StockPicking, self)._get_stock_barcode_data()
        
        # 1. Map existing move lines for quick lookup
        move_id_to_lines = {}
        if 'stock.move.line' in data.get('records', {}):
            for line in data['records']['stock.move.line']:
                mid = line.get('move_id')
                # Standardize Many2one values from read()
                if isinstance(mid, (list, tuple)) and mid:
                    mid = mid[0]
                elif isinstance(mid, models.BaseModel):
                    mid = mid.id

                if mid:
                    move_id_to_lines.setdefault(mid, []).append(line)

        # 2. Add virtual lines for moves without lines or with 0 reservation
        # This ensures they appear in the "To Process" list in Barcode app
        picking_virtual_ids = {}
        cache_ids = {
            'product.product': set(),
            'stock.location': set(),
            'uom.uom': set(),
        }

        for move in self.move_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
            lines = move_id_to_lines.get(move.id, [])

            # If no lines exist, create a virtual one to guide the user
            if not lines:
                v_id = -move.id - 1000000
                line_data = {
                    'id': v_id,
                    'dummy_id': v_id,
                    'virtual_id': v_id,
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'display_name': move.product_id.display_name,
                    'product_barcode': move.product_id.barcode,
                    'product_uom_id': move.product_uom.id,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                    'quantity': 0, # Done quantity starts at 0 for virtual lines
                    'picked': False,
                    'reserved_uom_qty': move.product_uom_qty, # Demand for Barcode UI
                    'product_uom_qty': move.product_uom_qty, # Demand for custom counter
                    'state': 'assigned' if move.state in ('confirmed', 'waiting') else move.state,
                    'tracking': move.product_id.tracking,
                    'customer_sales_order': move.customer_sales_order or '',
                    'customer_name': move.customer_name or '',
                    'package_id': False,
                    'result_package_id': False,
                    'owner_id': False,
                    'lot_id': False,
                    'lot_name': False,
                }
                data['records'].setdefault('stock.move.line', []).append(line_data)
                picking_virtual_ids.setdefault(move.picking_id.id, []).append(v_id)

                # Ensure dependencies are cached
                cache_ids['product.product'].add(move.product_id.id)
                cache_ids['stock.location'].update([move.location_id.id, move.location_dest_id.id])
                cache_ids['uom.uom'].add(move.product_uom.id)
            else:
                # For existing lines, just inject custom fields for display/counter
                # We STOPOVERWRITING reserved_uom_qty here to let Odoo's internal
                # reservation logic prevail for real lines.
                for line in lines:
                    line['product_uom_qty'] = move.product_uom_qty
                    line['customer_sales_order'] = move.customer_sales_order or ''
                    line['customer_name'] = move.customer_name or ''

        # 3. Link virtual lines back to picking data
        if picking_virtual_ids and 'stock.picking' in data.get('records', {}):
            for p_data in data['records']['stock.picking']:
                vids = picking_virtual_ids.get(p_data.get('id'))
                if vids:
                    current_ids = p_data.get('move_line_ids', [])
                    new_ids = list(current_ids) if isinstance(current_ids, (list, tuple)) else []
                    seen = set(new_ids)
                    new_ids.extend([vid for vid in vids if vid not in seen])
                    p_data['move_line_ids'] = new_ids

        # 4. Fill Cache
        for model, s_ids in cache_ids.items():
            if not s_ids: continue
            data['records'].setdefault(model, [])
            existing = {r['id'] for r in data['records'][model]}
            missing = s_ids - existing
            if missing:
                recs = self.env[model].search([('id', 'in', list(missing))])
                if recs:
                    fields = recs._get_fields_stock_barcode()
                    data['records'][model].extend(recs.read(fields, load=False))

        return data

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_fields_stock_barcode(self):
        # Ensure custom fields are available on move records for demand-only displays
        res = super(StockMove, self)._get_fields_stock_barcode()
        res.extend(['customer_sales_order', 'customer_name'])
        return res
